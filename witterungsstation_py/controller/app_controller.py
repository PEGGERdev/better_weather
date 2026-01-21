from __future__ import annotations
import threading, time
from typing import Optional, Tuple, Callable
from PySide6 import QtCore

from model.ports import WeatherSensorPort, OSSDPort, ClockPort
from model.dto import WeatherDTO, OSSDWriteResult
from model.db_client import DbClient
from model.ossd_change_writer import OSSDChangeWriter

from exception_handler import format_current_exception


class AppController:
    """
    Controller regelt Ablauf/Threads.
    - liest Hardware (Weather/OSSD)
    - persistiert OSSD nur bei Änderungen
    - postet Weather (best-effort)
    - aktualisiert View thread-sicher
    """

    def __init__(
        self,
        view,
        model_db: DbClient,
        weather: Optional[WeatherSensorPort],
        ossd: Optional[OSSDPort],
        clock: ClockPort,
        interval_sec: float = 30.0,
    ) -> None:
        self._v = view
        self._db = model_db
        self._weather = weather
        self._ossd = ossd
        self._clock = clock
        self._interval = float(interval_sec)

        self._stop = threading.Event()
        self._th: Optional[threading.Thread] = None

        # thread-sicheres Loggen in die View
        self._log = lambda msg: self._post(lambda m=str(msg): self._v.append_log(m))

        # Change-only Persistor (Logger ist jetzt thread-sicher!)
        self._persist = OSSDChangeWriter(self._db, logger=self._log)

        self._v.set_status("Bereit")

    # ---------------- lifecycle ----------------
    def start(self) -> None:
        if self._th and self._th.is_alive():
            self._v.append_log("Start ignoriert: läuft bereits.")
            return

        self._stop.clear()
        self._v.set_running_state(True)

        # Startzustände aus DB rekonstruieren (best-effort)
        try:
            states = self._persist.sync_from_backend()
            self._v.append_log(
                f"OSSD DB-Startzustand: ch0={states[0]}, ch1={states[1]}, ch2={states[2]}, ch3={states[3]}"
            )
        except Exception as e:
            # Stacktrace direkt jetzt formatieren (nicht erst später im GUI-Thread!)
            tb = format_current_exception(f"Warnung: OSSD-Startzustand unbekannt ({e})")
            self._v.append_log(tb)

        self._th = threading.Thread(target=self._loop, name="worker", daemon=True)
        self._th.start()
        self._v.append_log(f"Test gestartet (Intervall {self._interval:.1f}s).")

    def stop(self) -> None:
        self._stop.set()
        t = self._th
        if t and t.is_alive():
            t.join(timeout=2.0)
        self._th = None
        self._v.set_running_state(False)
        self._v.append_log("Gestoppt.")

    def test_once(self) -> None:
        try:
            self._tick()
            self._v.append_log("Einzeltest ok.")
        except Exception as e:
            tb = format_current_exception(f"Einzeltest fehlgeschlagen: {e}")
            self._log(tb)
            self._post(lambda m=str(e): self._v.show_error(m))

    # ---------------- loop ----------------
    def _loop(self) -> None:
        try:
            while not self._stop.is_set():
                self._tick()
                for _ in range(int(self._interval * 10)):
                    if self._stop.is_set():
                        break
                    time.sleep(0.1)
        except Exception as e:
            tb = format_current_exception(f"Worker-Loop abgebrochen: {e}")
            self._log(tb)
            self._post(lambda m=str(e): self._v.show_error(m))
        finally:
            self._post(lambda: self._v.set_running_state(False))

    def _tick(self) -> None:
        now = self._clock.now()

        # 1) OSSD lesen + nur bei Änderungen persistieren
        if self._ossd:
            st = self._ossd.read_state()
            if st:
                self._post(lambda s=st: self._v.update_ossd(s))
                res: OSSDWriteResult = self._persist.persist_if_changed(st, now)
                if res.posted or res.skipped:
                    self._post(lambda r=res: self._v.append_log(f"OSSD persist: +{r.posted}, = {r.skipped}"))
                # Für Diagramm einzelne Marker setzen
                for idx, val in enumerate(st):
                    changed = self._persist.last_sent[idx] is not None and self._persist.last_sent[idx] != val
                    if changed:
                        self._post(
                            lambda i=idx, ts=now: self._v.chart_add_ossd(
                                i, ts, f"LG{1 if i<2 else 2} OSSD{1 if i%2==0 else 2}"
                            )
                        )

        # 2) Wetter lesen + anzeigen + posten (best-effort)
        if self._weather:
            w = self._weather.read_weather()
            if w:
                dto = WeatherDTO(
                    temp=w.temp, preassure=w.preassure, light=w.light,
                    winds=w.winds, winddir=w.winddir, rain=w.rain,
                    humidity=w.humidity, time=getattr(w, "time", now)
                )
                self._post(lambda d=dto: self._v.update_weather(d.__dict__))
                try:
                    self._db.post_weather(dto)
                except Exception as e:
                    tb = format_current_exception(f"POST /weather fehlgeschlagen: {e}")
                    self._log(tb)

    # ---------------- gui invoke ----------------
    def _post(self, fn: Callable[[], None]) -> None:
        QtCore.QTimer.singleShot(0, fn)
