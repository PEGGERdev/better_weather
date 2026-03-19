from __future__ import annotations

from datetime import datetime

from data_handler.contracts import BaseOutputHandler


class CompositeOutputHandler(BaseOutputHandler):
    def __init__(self, *outputs: BaseOutputHandler) -> None:
        self._outputs = [output for output in outputs if output is not None]

    def emit_ossd(
        self,
        ts: datetime,
        lichtgitter_nr: int,
        ossd_nr: int,
        status: str,
    ) -> None:
        for output in self._outputs:
            output.emit_ossd(ts, lichtgitter_nr, ossd_nr, status)

    def emit_weather(
        self,
        ts: datetime,
        temp: float,
        pressure: float,
        humidity: float,
        winds: float,
        winddir: str,
        rain: float,
        light: float,
    ) -> None:
        for output in self._outputs:
            output.emit_weather(ts, temp, pressure, humidity, winds, winddir, rain, light)

    def close(self) -> None:
        for output in self._outputs:
            output.close()
