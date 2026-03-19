from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Optional, Tuple

from data_handler.contracts import BaseLifecycleService, BaseOssdReader, BaseOutputHandler, BaseWeatherReader, LogPort
from shared.parsers import OssdParser


class PipelineOrchestrator(BaseLifecycleService):
    """Generic runtime loop for sensor readers and output handlers."""

    def __init__(
        self,
        *,
        ossd_reader: Optional[BaseOssdReader],
        weather_reader: Optional[BaseWeatherReader],
        output: BaseOutputHandler,
        poll_sec: float,
        weather_interval_sec: float,
        log: LogPort,
    ) -> None:
        self._ossd_reader = ossd_reader
        self._weather_reader = weather_reader
        self._output = output
        self._poll = max(0.05, float(poll_sec))
        self._weather_interval = max(1.0, float(weather_interval_sec))
        self._log = log
        self._stop = False
        self._prev: list[Optional[bool]] = [None, None, None, None]

    @staticmethod
    def _channel_meta(idx: int) -> Tuple[int, int]:
        return OssdParser.channel_meta(idx)

    def _process_ossd(self) -> None:
        if self._ossd_reader is None:
            return
        state = self._ossd_reader.read()
        if state is None:
            return

        now = datetime.now(UTC)
        for idx, value in enumerate(state):
            previous = self._prev[idx]
            if previous is None:
                lg, on = self._channel_meta(idx)
                status = OssdParser.status_to_string(value)
                self._output.emit_ossd(now, lg, on, status)
                self._prev[idx] = value
                continue
            if previous == value:
                continue

            lg, on = self._channel_meta(idx)
            status = OssdParser.status_to_string(value)
            self._output.emit_ossd(now, lg, on, status)
            self._prev[idx] = value

    def _process_weather(self) -> None:
        if self._weather_reader is None:
            return
        data = self._weather_reader.read()
        if data is None:
            return

        now = datetime.now(UTC)
        self._output.emit_weather(
            ts=now,
            temp=float(data["temp"]),
            pressure=float(data["pressure"]),
            humidity=float(data["humidity"]),
            winds=float(data["winds"]),
            winddir=str(data["winddir"]),
            rain=float(data["rain"]),
            light=float(data["light"]),
        )

    def run(self) -> None:
        next_weather = time.monotonic()
        self._log(
            f"PipelineOrchestrator running: poll={self._poll:.2f}s weather_interval={self._weather_interval:.0f}s"
        )
        while not self._stop:
            self._process_ossd()
            now_mono = time.monotonic()
            if now_mono >= next_weather:
                self._process_weather()
                next_weather = now_mono + self._weather_interval
            time.sleep(self._poll)

    def stop(self) -> None:
        self._stop = True

    def close(self) -> None:
        self._stop = True
