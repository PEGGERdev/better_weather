from __future__ import annotations

from datetime import UTC, datetime
import unittest

from data_handler.contracts import BaseOssdReader, BaseOutputHandler, BaseWeatherReader
from data_handler.orchestrator import PipelineOrchestrator


class TestOssdReader(BaseOssdReader):
    def __init__(self) -> None:
        self._states = [
            (True, True, True, True),
            (True, False, True, True),
        ]
        self._index = 0

    def read(self):
        if self._index >= len(self._states):
            return self._states[-1]
        value = self._states[self._index]
        self._index += 1
        return value


class TestWeatherReader(BaseWeatherReader):
    def __init__(self) -> None:
        self._sent = False

    def read(self):
        if self._sent:
            return None
        self._sent = True
        return {
            "temp": 21.1,
            "pressure": 1009.2,
            "humidity": 50.0,
            "winds": 2.0,
            "winddir": "NE",
            "rain": 0.0,
            "light": 120.0,
        }


class CaptureOutput(BaseOutputHandler):
    def __init__(self) -> None:
        self.ossd_events: list[tuple[int, int, str]] = []
        self.weather_events: list[dict] = []

    def emit_ossd(self, ts: datetime, lichtgitter_nr: int, ossd_nr: int, status: str) -> None:
        self.ossd_events.append((lichtgitter_nr, ossd_nr, status))

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
        self.weather_events.append(
            {
                "temp": temp,
                "pressure": pressure,
                "humidity": humidity,
                "winds": winds,
                "winddir": winddir,
                "rain": rain,
                "light": light,
            }
        )


class PipelineOrchestratorTests(unittest.TestCase):
    def test_pipeline_processes_reader_data_without_ui(self) -> None:
        out = CaptureOutput()
        ossd_reader = TestOssdReader()
        weather_reader = TestWeatherReader()
        orch = PipelineOrchestrator(
            ossd_reader=ossd_reader,
            weather_reader=weather_reader,
            output=out,
            poll_sec=0.01,
            weather_interval_sec=0.01,
            log=lambda message: None,
        )

        # Run a few internal ticks directly (no manual clicking).
        orch._process_ossd()
        orch._process_ossd()
        orch._process_weather()

        self.assertEqual(len(out.ossd_events), 5)
        self.assertEqual(out.ossd_events[0], (1, 1, "O"))
        self.assertEqual(out.ossd_events[1], (1, 2, "O"))
        self.assertEqual(out.ossd_events[2], (2, 1, "O"))
        self.assertEqual(out.ossd_events[3], (2, 2, "O"))
        self.assertEqual(out.ossd_events[4], (1, 2, "E"))
        self.assertEqual(len(out.weather_events), 1)
        self.assertEqual(out.weather_events[0]["winddir"], "NE")


if __name__ == "__main__":
    unittest.main()
