from __future__ import annotations

"""
Witterungstester – AppController (Orchestrator)

Role
- Polls OSSD live (UI updates immediately).
- Records every OSSD change (WAL immediately, backend only every flush interval).
- Reads weather only on flush interval (UI updates on interval).
- Redraws chart only on flush interval (performance).

Threading
- Worker thread runs polling + flush schedule.
- All UI interactions are marshalled to the GUI thread via Qt signal.

Design goals
- SOLID: isolate responsibilities (WAL store, OSSD tracking).
- DRY  : single mapping for channel -> (lichtgitter, ossd, label).
- KISS : keep orchestration in one place, helper classes small and local.
"""

import threading
import time
import json
from pathlib import Path
from typing import Optional, Callable, List, Tuple, Protocol

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


# ---------------- View contract (documentation / DIP) ----------------
class AppViewPort(Protocol):
    def set_status(self, text: str) -> None: ...
    def set_running_state(self, running: bool) -> None: ...
    def show_error(self, msg: str) -> None: ...
    def append_log(self, line: str) -> None: ...
    def update_ossd(self, st: Tuple[bool, bool, bool, bool]) -> None: ...
    def update_weather(self, payload: dict) -> None: ...
    def chart_add_ossd(self, channel_idx: int, ts, label: str) -> None: ...
    def chart_redraw(self) -> None: ...


class _GuiInvoker(QtCore.QObject):
    """
    Thread-safe bridge: worker thread -> GUI thread.

    WHY
    - Worker thread must never touch Qt widgets directly.
    - A Qt signal ensures queued execution on the GUI thread.
    """
    invoke = QtCore.Signal(object)


def _channel_meta(idx: int) -> Tuple[int, int, str]:
    """
    Maps channel index (0..3) to (lichtgitterNr, ossdNr, label).
    """
    lg = 1 if idx < 2 else 2
    on = 1 if idx % 2 == 0 else 2
    return lg, on, f"LG{lg} OSSD{on}"


class WalJsonlStore:
    """
    Minimal jsonl WAL store for OSSD events.

    Contract
    - append(): best-effort, must never crash app
    - load()  : best-effort, returns [] on failure
    - rewrite(): best-effort, keeps only pending backlog
    """

    def __init__(self, path: Path):
        self._path = path

    def append(self, entry: OSSDEntryDTO) -> None:
        try:
            rec = {
                "time": entry.time.isoformat(),
                "lichtgitterNr": entry.lichtgitterNr,
                "ossdNr": entry.ossdNr,
                "ossdStatus": entry.ossdStatus,
            }
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            # NOTE: WAL is a safety net; it must never break the app.
            pass

    def load(self, clock: ClockPort) -> List[OSSDEntryDTO]:
        if not self._path.exists():
            return []
        try:
            from datetime import datetime
            out: List[OSSDEntryDTO] = []
            with self._path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    ts = obj.get("time")
                    dt = datetime.fromisoformat(ts) if isinstance(ts, str) else clock.now()
                    out.append(
                        OSSDEntryDTO(
                            time=dt,
                            lichtgitterNr=int(obj.get("lichtgitterNr", 0)),
                            ossdNr=int(obj.get("ossdNr", 0)),
                            ossdStatus=str(obj.get("ossdStatus", "E")),
                        )
                    )
            return out
        except Exception:
            return []

    def rewrite(self, entries: List[OSSDEntryDTO]) -> None:
        try:
            if not entries:
                if self._path.exists():
                    self._path.unlink(missing_ok=True)
                return

            tmp = self._path.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                for entry in entries:
                    rec = {
                        "time": entry.time.isoformat(),
                        "lichtgitterNr": entry.lichtgitterNr,
                        "ossdNr": entry.ossdNr,
                        "ossdStatus": entry.ossdStatus,
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            tmp.replace(self._path)
        except Exception:
            pass


class OssdStateTracker:
    """
    Tracks OSSD state for:
    - UI updates (only on change)
    - Event generation (only on change, no event on first observation)

    INVARIANT
    - prev[idx] is last known state for change detection; None means uninitialized.
    """

    def __init__(self) -> None:
        self.prev: List[Optional[bool]] = [None, None, None, None]
        self.ui_last: Optional[Tuple[bool, bool, bool, bool]] = None

    def seed_from_backend(self, states: List[Optional[bool]]) -> Tuple[bool, bool, bool, bool]:
        self.prev = list(states)
        ui_state = tuple(bool(x) if x is not None else False for x in states)  # None -> red
        self.ui_last = ui_state
        return ui_state  # for immediate UI update

    def process(
        self,
        now,
        st: Tuple[bool, bool, bool, bool],
    ) -> Tuple[Optional[Tuple[bool, bool, bool, bool]], List[Tuple[int, object, str]], List[OSSDEntryDTO]]:
        # UI update only if changed
        ui_update: Optional[Tuple[bool, bool, bool, bool]] = None
        if self.ui_last != st:
            self.ui_last = st
            ui_update = st

        chart_events: List[Tuple[int, object, str]] = []
        new_entries: List[OSSDEntryDTO] = []

        for idx, val in enumerate(st):
            prev = self.prev[idx]

            if prev is None:
                self.prev[idx] = val
                continue

            if prev != val:
                lg, on, label = _channel_meta(idx)
                chart_events.append((idx, now, label))
                new_entries.append(
                    OSSDEntryDTO(
                        time=now,
                        lichtgitterNr=lg,
                        ossdNr=on,
                        ossdStatus=("O" if val else "E"),
                    )
                )
                self.prev[idx] = val

        return ui_update, chart_events, new_entries


class AppController:
    """
    See module docstring for behavior details.
    """

    def __init__(
        self,
        view: AppViewPort,
        model_db: DbClient,
        weather: Optional[WeatherSensorPort],
        ossd: Optional[OSSDPort],
        clock: ClockPort,
        interval_sec: float = 30.0,
        poll_sec: float = 0.05,
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

        # Optional initial sync helper (backend reconstruction)
        self._persist = OSSDChangeWriter(self._db, logger=self._v.append_log)

        self._tracker = OssdStateTracker()
        self._queue: List[OSSDEntryDTO] = []

        self._wal_store = WalJsonlStore(Path(wal_path))

        self._invoker = _GuiInvoker()
        self._invoker.invoke.connect(self._invoke_safe)

        self._v.set_status("Bereit")

    # ---------------- lifecycle ----------------
    def start(self) -> None:
        if self._th and self._th.is_alive():
            self._v.append_log("Start ignoriert: läuft bereits.")
            return

        self._stop.clear()
        self._v.set_running_state(True)

        # Load WAL into queue (so every change stays recorded)
        loaded = self._wal_store.load(self._clock)
        if loaded:
            self._queue.extend(loaded)
            self._v.append_log(f"WAL geladen: {len(loaded)} OSSD-Events pending.")

        # Reconstruct start state from backend (best-effort)
        try:
            states = self._persist.sync_from_backend()
            if isinstance(states, list) and len(states) == 4:
                ui_state = self._tracker.seed_from_backend(states)
                self._post(lambda s=ui_state: self._v.update_ossd(s))

            self._v.append_log(
                f"OSSD DB-Startzustand: ch0={states[0]}, ch1={states[1]}, ch2={states[2]}, ch3={states[3]}"
            )
        except Exception as e:
            self._v.append_log(format_current_exception(f"Warnung: OSSD-Startzustand unbekannt ({e})"))

        self._th = threading.Thread(target=self._loop, name="worker", daemon=True)
        self._th.start()

        self._v.append_log(
            f"Live OSSD Polling {self._poll:.2f}s | Wetter+DB Flush alle {self._flush_sec:.0f}s | WAL={self._wal_store._path}"
        )

    def stop(self) -> None:
        self._stop.set()
        t = self._th
        if t and t.is_alive():
            t.join(timeout=2.0)
        self._th = None
        self._v.set_running_state(False)
        self._v.append_log("Gestoppt.")

        # NOTE: No extra DB write on stop (keep "only every 30s" true).
        # WAL keeps all events and will be flushed on next start/flush.

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
                self._tick_ossd_live()

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
        if st is None:
            return

        ui_update, chart_events, new_entries = self._tracker.process(now, st)

        if ui_update is not None:
            self._post(lambda s=ui_update: self._v.update_ossd(s))

        for idx, ts, label in chart_events:
            self._post(lambda i=idx, t=ts, l=label: self._v.chart_add_ossd(i, t, l))

        for entry in new_entries:
            self._queue.append(entry)
            self._wal_store.append(entry)

    # ---------------- flush (every interval) ----------------
    def _flush(self) -> None:
        # 1) Weather only on interval
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
                    self._db.post_weather(dto)
            except Exception as e:
                self._post(lambda: self._v.append_log(format_current_exception(f"Flush Weather fehlgeschlagen: {e}")))

        # 2) OSSD events batched to backend
        if not self._queue:
            self._post(lambda: self._v.append_log("DB-Flush: ossd queued=0"))
        else:
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

            self._queue = remaining + self._queue
            self._wal_store.rewrite(self._queue)

            self._post(lambda: self._v.append_log(
                f"DB-Flush: ossd ok={ok} fail={fail} remaining={len(self._queue)}"
            ))

        # 3) Chart redraw only on interval
        if hasattr(self._v, "chart_redraw"):
            self._post(self._v.chart_redraw)

    # ---------------- GUI invoke ----------------
    @QtCore.Slot(object)
    def _invoke_safe(self, fn_obj: object) -> None:
        try:
            if callable(fn_obj):
                fn_obj()
        except Exception:
            # NOTE: Logging must never kill the UI thread.
            try:
                self._v.append_log(format_current_exception("GUI invoke fehlgeschlagen"))
            except Exception:
                pass

    def _post(self, fn: Callable[[], None]) -> None:
        """
        Thread-safe GUI dispatch.
        """
        try:
            self._invoker.invoke.emit(fn)
        except Exception:
            try:
                QtCore.QTimer.singleShot(0, fn)
            except Exception:
                pass
