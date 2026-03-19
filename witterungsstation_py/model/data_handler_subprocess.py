from __future__ import annotations

import subprocess
import threading
from typing import Any, Callable, Optional, cast

from model.data_handler_command import DataHandlerCommand
from model.dto import OSSDEntryDTO, WeatherDTO
from model.ipc_event_parser import IpcEventParser


class DataHandlerSubprocess:
    def __init__(
        self,
        *,
        serial_port: str | None = None,
        serial_baud: int | None = None,
        hid_vid: int | None = None,
        hid_pid: int | None = None,
        poll_sec: float | None = None,
        interval_sec: float | None = None,
        backend_base: str | None = None,
        output_mode: str | None = None,
        disable_weather: bool = False,
        on_ossd: Optional[Callable[[OSSDEntryDTO], None]] = None,
        on_weather: Optional[Callable[[WeatherDTO], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._serial_port = serial_port
        self._serial_baud = serial_baud
        self._hid_vid = hid_vid
        self._hid_pid = hid_pid
        self._poll_sec = poll_sec
        self._interval_sec = interval_sec
        self._backend_base = backend_base
        self._output_mode = str(output_mode or "backend").strip().lower()
        self._disable_weather = bool(disable_weather)
        self._on_ossd = on_ossd
        self._on_weather = on_weather
        self._on_log = on_log
        self._command = DataHandlerCommand(
            serial_port=serial_port,
            serial_baud=serial_baud,
            hid_vid=hid_vid,
            hid_pid=hid_pid,
            poll_sec=poll_sec,
            interval_sec=interval_sec,
            backend_base=backend_base,
            output_mode=output_mode,
            disable_weather=disable_weather,
        )
        self._parser = IpcEventParser()

        self._proc: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._events_lock = threading.Lock()
        self._ossd_events: list[OSSDEntryDTO] = []
        self._weather_events: list[WeatherDTO] = []

    def _handle_line(self, line: str) -> None:
        parsed = self._parser.parse_line(line)
        if parsed is None:
            if self._on_log:
                self._on_log(line)
            return

        if parsed.kind == "ossd":
            entry = cast(OSSDEntryDTO, parsed.payload)
            with self._events_lock:
                self._ossd_events.append(entry)
            if self._on_ossd:
                self._on_ossd(entry)
            return

        if parsed.kind == "weather":
            weather = cast(WeatherDTO, parsed.payload)
            with self._events_lock:
                self._weather_events.append(weather)
            if self._on_weather:
                self._on_weather(weather)
            return

        if self._on_log:
            self._on_log(line)

    def drain_ossd_events(self) -> list[OSSDEntryDTO]:
        with self._events_lock:
            out = list(self._ossd_events)
            self._ossd_events.clear()
            return out

    def drain_weather_events(self) -> list[WeatherDTO]:
        with self._events_lock:
            out = list(self._weather_events)
            self._weather_events.clear()
            return out

    def _reader_loop(self) -> None:
        if not self._proc or not self._proc.stdout:
            return
        stdout = cast(Any, self._proc.stdout)
        try:
            while not self._stop_event.is_set():
                line = stdout.readline()
                if not line:
                    break
                text = str(line).rstrip("\n\r")
                if text:
                    try:
                        self._handle_line(text)
                    except Exception as exc:
                        if self._on_log:
                            self._on_log(f"DataHandlerSubprocess: parse error: {exc}")
        except Exception as exc:
            if self._on_log:
                self._on_log(f"DataHandlerSubprocess reader error: {exc}")

    def start(self) -> bool:
        if self._proc is not None:
            return True

        env = self._command.build_env()

        try:
            self._proc = subprocess.Popen(
                self._command.argv(),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            if self._on_log:
                self._on_log(f"DataHandlerSubprocess: failed to start: {exc}")
            return False

        self._stop_event.clear()
        self._reader_thread = threading.Thread(
            target=self._reader_loop,
            name="data-handler-reader",
            daemon=True,
        )
        self._reader_thread.start()

        if self._on_log:
            self._on_log("DataHandlerSubprocess started")
        return True

    def stop(self) -> None:
        self._stop_event.set()

        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
            try:
                self._proc.wait(timeout=2.0)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1.0)
        self._reader_thread = None

        if self._on_log:
            self._on_log("DataHandlerSubprocess stopped")

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None
