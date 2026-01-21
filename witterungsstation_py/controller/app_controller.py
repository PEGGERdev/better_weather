from __future__ import annotations
import threading, time, json
from typing import Optional, Tuple, Callable, List
from pathlib import Path
from PySide6 import QtCore

from model.ports import WeatherSensorPort, OSSDPort, ClockPort
from model.dto import WeatherDTO, OSSDEntryDTO
from model.db_client import DbClient
from model.ossd_change_writer import OSSDChangeWriter

try:
    from exception_handler import format_current_exception
except Exception:
    def format_current_exception(msg: str) -> str:
        import traceback
        return f"{msg}\n{traceback.format_exc()}"


class AppController:
    """
    - OSSD/Lichtgitter: live lesen + UI sofort updaten + jede Änderung als Event festhalten
      => Events werden sofort in WAL (jsonl) geschrieben und nur alle flush_sec ans Backend gepostet.
    - Wetter: nur alle flush_sec messen + UI updaten + posten (dazwischen ignoriert)
    """

    def __init__(
        self,
        view,
        model_db: DbClient,
        weather: Optional[WeatherSensorPort],
        ossd: Optional[OSSDPort],
        clock: ClockPort,
        interval_sec: float = 30.0,      # DB Flush + Wetter Messintervall
        poll_sec: float = 0.05,          # OSSD Polling (live)
        wal_path: str = "ossd_events_wal.jsonl",
    ) -> None:
        self._v = view
        self._db = model_db
        self._weather = weather
        self._ossd = ossd
        self._clock = clock

        self._flush_sec = float(interval_sec)
        self._poll = max(0.02, float(poll_sec))

        self._stop = threading.Event()
        self._th: Optional[threading.Thread] = None

        # Nur fürs Initial-Sync (optional)
        self._persist = OSSDChangeWriter(self._db, logger=self._v.append_log)

        # Live-State für Change-Detection
        self._prev_ossd: List[Optional[bool]] = [None, None, None, None]

        # Event-Queue + WAL
        self._queue: List[OSSDEntryDTO] = []
        self._wal = Path(wal_path)

        self._v.set_status("Bereit")

    # ---------------- lifecycle ----------------
    def start(self) -> None:
        if self._th and self._th.is_alive():
            self._v.append_log("Start ignoriert: läuft bereits.")
            return

        self._stop.clear()
        self._v.set_running_state(True)

        # WAL laden (damit wirklich jede Änderung "festgehalten" bleibt)
        self._load_wal_into_queue()

        # Startzustände aus DB rekonstruieren (best-effort)
        try:
            states = self._persist.sync_from_backend()
            if isinstance(states, list) and len(states) == 4:
                self._prev_ossd = list(states)
            self._v.append_log(
                f"OSSD DB-Startzustand: ch0={states[0]}, ch1={states[1]}, ch2={states[2]}, ch3={states[3]}"
            )
        except Exception as e:
            self._v.append_log(format_current_exception(f"Warnung: OSSD-Startzustand unbekannt ({e})"))

        self._th = threading.Thread(target=self._loop, name="worker", daemon=True)
        self._th.start()
        self._v.append_log(
            f"Live OSSD Polling {self._poll:.2f}s | Wetter+DB Flush alle {self._flush_sec:.0f}s | WAL={self._wal}"
        )

    def stop(self) -> None:
        self._stop.set()
        t = self._th
        if t and t.is_alive():
            t.join(timeout=2.0)
        self._th = None
        self._v.set_running_state(False)
        self._v.append_log("Gestoppt.")

        # Wichtig: KEIN extra DB-Write beim Stop (damit 'nur alle 30s' wirklich gilt)
        # OSSD-Events sind durch WAL trotzdem "festgehalten" und werden beim nächsten Start/Flush gesendet.

    def test_once(self) -> None:
        try:
            self._tick_ossd_live()
            self._v.append_log("Einzeltest ok.")
        except Exception as e:
            self._post(lambda: self._v.show_error(str(e)))
            self._v.append_log(format_current_exception(f"Einzeltest fehlgeschlagen: {e}"))

    # ---------------- main loop ----------------
    def _loop(self) -> None:
        next_flush = time.monotonic() + self._flush_sec
        try:
            while not self._stop.is_set():
                # OSSD live
                self._tick_ossd_live()

                # Flush: Wetter messen + DB schreiben (gebündelt)
                now_m = time.monotonic()
                if now_m >= next_flush:
                    self._flush()
                    next_flush = now_m + self._flush_sec

                time.sleep(self._poll)

        except Exception as e:
            self._post(lambda: self._v.show_error(str(e)))
            self._v.append_log(format_current_exception(f"Worker-Loop abgebrochen: {e}"))
        finally:
            self._post(lambda: self._v.set_running_state(False))

    # ---------------- OSSD live tick ----------------
    def _tick_ossd_live(self) -> None:
        if not self._ossd:
            return

        now = self._clock.now()
        st = self._ossd.read_state()
        if not st:
            return

        # UI sofort aktualisieren
        self._post(lambda s=st: self._v.update_ossd(s))

        # Jede Änderung als Event festhalten (nicht nur finalen Stand)
        for idx, val in enumerate(st):
            prev = self._prev_ossd[idx]

            # Initialisierung: noch kein Event
            if prev is None:
                self._prev_ossd[idx] = val
                continue

            if prev != val:
                # Diagramm-Event sofort
                self._post(
                    lambda i=idx, ts=now: self._v.chart_add_ossd(
                        i, ts, f"LG{1 if i<2 else 2} OSSD{1 if i%2==0 else 2}"
                    )
                )

                # Queue + WAL (sofort!)
                lg = 1 if idx < 2 else 2
                on = 1 if idx % 2 == 0 else 2
                entry = OSSDEntryDTO(
                    time=now,
                    lichtgitterNr=lg,
                    ossdNr=on,
                    ossdStatus=("O" if val else "E"),
                )
                self._queue.append(entry)
                self._append_wal(entry)

                self._prev_ossd[idx] = val

    # ---------------- flush (alle 30s) ----------------
    def _flush(self) -> None:
        # 1) Wetter nur im Intervall messen + posten (dazwischen ignoriert)
        if self._weather:
            try:
                now = self._clock.now()
                w = self._weather.read_weather()
                if w:
                    dto = WeatherDTO(
                        temp=w.temp, preassure=w.preassure, light=w.light,
                        winds=w.winds, winddir=w.winddir, rain=w.rain,
                        humidity=w.humidity, time=getattr(w, "time", now)
                    )
                    self._post(lambda d=dto: self._v.update_weather(d.__dict__))
                    self._db.post_weather(dto)  # best-effort (DbClient loggt bei Exception)
            except Exception as e:
                self._post(lambda: self._v.append_log(format_current_exception(f"Flush Weather fehlgeschlagen: {e}")))

        # 2) OSSD-Events gebündelt ans Backend (jede Änderung)
        if not self._queue:
            self._post(lambda: self._v.append_log("DB-Flush: ossd queued=0"))
            return

        to_send = self._queue
        self._queue = []

        ok = 0
        fail = 0
        remaining: List[OSSDEntryDTO] = []

        for entry in to_send:
            try:
                self._db.post_ossd(entry)
                ok += 1
            except Exception as e:
                fail += 1
                remaining.append(entry)
                self._post(lambda: self._v.append_log(format_current_exception(f"Flush OSSD fehlgeschlagen: {e}")))

        # Backlog behalten
        self._queue = remaining + self._queue

        # WAL auf den aktuellen Backlog reduzieren (damit nichts verloren geht)
        self._rewrite_wal(self._queue)

        self._post(lambda: self._v.append_log(
            f"DB-Flush: ossd ok={ok} fail={fail} remaining={len(self._queue)}"
        ))

    # ---------------- WAL helpers ----------------
    def _append_wal(self, entry: OSSDEntryDTO) -> None:
        try:
            rec = {
                "time": entry.time.isoformat(),
                "lichtgitterNr": entry.lichtgitterNr,
                "ossdNr": entry.ossdNr,
                "ossdStatus": entry.ossdStatus,
            }
            self._wal.parent.mkdir(parents=True, exist_ok=True)
            with self._wal.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            # WAL ist nur zusätzlicher Schutz; darf nie die App brechen
            pass

    def _load_wal_into_queue(self) -> None:
        if not self._wal.exists():
            return
        try:
            from datetime import datetime
            loaded = 0
            with self._wal.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    ts = obj.get("time")
                    dt = datetime.fromisoformat(ts) if isinstance(ts, str) else self._clock.now()
                    self._queue.append(
                        OSSDEntryDTO(
                            time=dt,
                            lichtgitterNr=int(obj.get("lichtgitterNr", 0)),
                            ossdNr=int(obj.get("ossdNr", 0)),
                            ossdStatus=str(obj.get("ossdStatus", "E")),
                        )
                    )
                    loaded += 1
            if loaded:
                self._v.append_log(f"WAL geladen: {loaded} OSSD-Events pending.")
        except Exception as e:
            self._v.append_log(format_current_exception(f"WAL laden fehlgeschlagen: {e}"))

    def _rewrite_wal(self, entries: List[OSSDEntryDTO]) -> None:
        try:
            if not entries:
                # optional: leere Datei entfernen
                if self._wal.exists():
                    self._wal.unlink(missing_ok=True)  # py>=3.8
                return

            tmp = self._wal.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                for entry in entries:
                    rec = {
                        "time": entry.time.isoformat(),
                        "lichtgitterNr": entry.lichtgitterNr,
                        "ossdNr": entry.ossdNr,
                        "ossdStatus": entry.ossdStatus,
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            tmp.replace(self._wal)
        except Exception:
            pass

    # ---------------- gui invoke ----------------
    def _post(self, fn: Callable[[], None]) -> None:
        QtCore.QTimer.singleShot(0, fn)
