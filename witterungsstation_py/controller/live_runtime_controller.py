from __future__ import annotations

import time
from typing import Callable, Optional, Protocol

from datetime import UTC, datetime

from model.dto import WeatherDTO, WitterungsstationPyStateDTO

from controller.backend_sync import BackendSync
from controller.local_ossd_relay import DataHandlerDrainPort, LocalOssdRelay
from controller.local_weather_relay import DataHandlerWeatherDrainPort, LocalWeatherRelay
from controller.runtime_loop import RuntimeLoop
from model.ports import TelemetryPort
class DataHandlerPort(DataHandlerDrainPort, DataHandlerWeatherDrainPort, Protocol):
    def start(self) -> bool: ...
    def stop(self) -> None: ...
    def is_running(self) -> bool: ...


class WeatherLiveReaderPort(Protocol):
    def open(self) -> bool: ...
    def close(self) -> None: ...
    def read(self) -> Optional[dict]: ...


class LiveRuntimeController:
    """GUI controller using canonical data_handler service + backend polling."""

    TEST_ONCE_TIMEOUT_SEC = 8.0

    def __init__(
        self,
        view,
        model_db: TelemetryPort,
        data_handler: DataHandlerPort,
        weather_live_reader: Optional[WeatherLiveReaderPort] = None,
        poll_sec: float = 1.0,
        backend_interval_sec: float = 30.0,
        post: Optional[Callable[[Callable[[], None]], None]] = None,
    ) -> None:
        self._v = view
        self._db = model_db
        self._data_handler = data_handler
        self._weather_live_reader = weather_live_reader
        self._post_fn = post
        self._started_handler = False
        self._local_ossd = LocalOssdRelay(
            data_handler=self._data_handler,
            view=self._v,
            post=self._post,
        )
        self._local_weather = LocalWeatherRelay(
            data_handler=self._data_handler,
            view=self._v,
            post=self._post,
        )
        self._backend_sync = BackendSync(
            view=self._v,
            model_db=self._db,
            post=self._post,
            weather_live_reader=self._weather_live_reader,
            backend_interval_sec=backend_interval_sec,
            publish_live_weather=True,
            sync_backend_ossd=False,
        )
        self._runtime = RuntimeLoop(poll_sec=poll_sec, step=lambda: None if self._poll_once() else None)

        self._v.set_status("Bereit")
        self._publish_mode = self._resolve_telemetry_mode()
        self._post(lambda: self._v.set_telemetry_mode(self._publish_mode))

    def _resolve_telemetry_mode(self) -> str:
        if self._weather_live_reader is None:
            return "Subprozess liefert Live-Daten; App schreibt Backend im Intervall"
        return "Fallback-Direktleser schreibt Wetter; Backend bleibt Kanon"

    def start(self) -> None:
        if self._runtime.is_running():
            self._post(lambda: self._v.append_log("Start ignoriert: läuft bereits."))
            return

        self._ensure_inputs_running()

        self._backend_sync.reset_poll_schedule()
        self._post(lambda: self._v.set_running_state(True))
        if self._runtime.start():
            self._publish_runtime_state("start")

    def stop(self) -> None:
        was_running = self._runtime.is_running()
        self._runtime.stop()

        if self._started_handler:
            self._data_handler.stop()
            self._started_handler = False

        if self._weather_live_reader is not None:
            try:
                self._weather_live_reader.close()
            except Exception as exc:
                self._post(lambda: self._v.append_log(f"Weather-live-reader stop Fehler: {exc}"))

        self._post(lambda: self._v.set_running_state(False))
        self._post(lambda: self._v.append_log("Gestoppt."))
        if was_running:
            self._publish_runtime_state("stop")

    def test_once(self) -> None:
        self._ensure_inputs_running()
        self._backend_sync.reset_poll_schedule()
        self._post(lambda: self._v.append_log("Test 1x: lese Wetterdaten und versuche Backend-Upload..."))
        deadline = time.monotonic() + self.TEST_ONCE_TIMEOUT_SEC
        while True:
            got_weather = self._poll_once(publish_local_weather=True)
            if got_weather or time.monotonic() >= deadline:
                break
            time.sleep(0.1)
        if not got_weather:
            self._post(lambda: self._v.append_log("Test 1x: keine Wetterdaten empfangen."))

    def _ensure_inputs_running(self) -> None:
        if not self._data_handler.is_running():
            self._started_handler = self._data_handler.start()
            self._post(lambda: self._v.append_log("Data-handler gestartet." if self._started_handler else "Data-handler konnte nicht gestartet werden."))
            if self._started_handler:
                self._publish_mode = "Subprozess liefert Live-Daten; App schreibt Backend im Intervall"
                self._post(lambda: self._v.set_telemetry_mode(self._publish_mode))

        if self._weather_live_reader is not None:
            try:
                self._weather_live_reader.open()
            except Exception as exc:
                self._post(lambda: self._v.append_log(f"Weather-live-reader start Fehler: {exc}"))
                self._publish_mode = "Fallback-Direktleser aktiv"
                self._post(lambda: self._v.set_telemetry_mode(self._publish_mode))

    def _poll_once(self, publish_local_weather: bool = False) -> bool:
        try:
            local_weather_events = self._local_weather.apply()
            if publish_local_weather:
                self._publish_local_weather(local_weather_events)
            local_ossd_events = self._local_ossd.apply()
            self._publish_local_ossd(local_ossd_events)
            latest_local_weather = None if publish_local_weather else (local_weather_events[-1] if local_weather_events else None)
            got_live_weather = self._backend_sync.poll(
                has_local_ossd_events=bool(local_ossd_events),
                latest_local_weather=latest_local_weather,
            )
            return bool(local_weather_events) or bool(got_live_weather)
        except Exception as exc:
            self._post(lambda: self._v.append_log(f"Polling Fehler: {exc}"))
            return False

    def _publish_local_weather(self, events: list[WeatherDTO]) -> None:
        for entry in events:
            try:
                self._db.post_weather(entry)
                self._post(lambda: self._v.append_log("Test 1x: Wetterdaten an Backend gesendet."))
            except Exception as exc:
                self._post(lambda: self._v.append_log(f"Test 1x: Backend-Upload fehlgeschlagen: {exc}"))
                return

    def _publish_local_ossd(self, events) -> None:
        for entry in events:
            try:
                self._db.post_ossd(entry)
            except Exception as exc:
                self._post(lambda: self._v.append_log(f"OSSD Backend-Upload fehlgeschlagen: {exc}"))
                return

    def _publish_runtime_state(self, state: str) -> None:
        try:
            self._db.post_witterungsstation_py_state(
                WitterungsstationPyStateDTO(
                    time=datetime.now(UTC),
                    state="start" if state == "start" else "stop",
                )
            )
        except Exception as exc:
            self._post(lambda: self._v.append_log(f"Runtime-State Backend-Upload fehlgeschlagen: {exc}"))

    def _post(self, fn) -> None:
        try:
            if self._post_fn is not None:
                self._post_fn(fn)
            else:
                fn()
        except Exception:
            try:
                fn()
            except Exception:
                pass
