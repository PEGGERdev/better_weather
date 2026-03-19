from __future__ import annotations

from datetime import UTC, datetime
import os
from tempfile import TemporaryDirectory
import unittest

from model.api_registry import API_ENDPOINTS
from model.dto import OSSDEntryDTO, WeatherDTO, WitterungsstationPyStateDTO
from model.telemetry_service import TelemetryService


class FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def request(self, endpoint_key: str, **kwargs):
        self.calls.append((endpoint_key, kwargs))
        if endpoint_key in (API_ENDPOINTS["WEATHER_LIST"], API_ENDPOINTS["OSSD_LIST"], API_ENDPOINTS["WITTERUNGSSTATION_PY_STATE_LIST"]):
            return []
        return {"id": "ok"}


class TestTelemetryService(TelemetryService):
    pass


class TelemetryServiceCommunicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self._old_wal = os.environ.get("TELEMETRY_WAL_PATH")
        os.environ["TELEMETRY_WAL_PATH"] = os.path.join(self._tmpdir.name, "telemetry-test.jsonl")

    def tearDown(self) -> None:
        if self._old_wal is None:
            os.environ.pop("TELEMETRY_WAL_PATH", None)
        else:
            os.environ["TELEMETRY_WAL_PATH"] = self._old_wal
        self._tmpdir.cleanup()

    def test_post_weather_maps_payload_and_endpoint(self) -> None:
        gateway = FakeGateway()
        service = TestTelemetryService(gateway)

        service.post_weather(
            WeatherDTO(
                temp=18.5,
                pressure=1008.2,
                light=123.0,
                winds=2.7,
                winddir="SW",
                rain=0.0,
                humidity=56.0,
                time=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )

        endpoint, options = gateway.calls[0]
        self.assertEqual(endpoint, API_ENDPOINTS["WEATHER_CREATE"])
        payload = options["body"]
        self.assertEqual(payload["pressure"], 1008.2)
        self.assertEqual(payload["winddir"], "SW")

    def test_invalid_weather_is_skipped(self) -> None:
        gateway = FakeGateway()
        service = TestTelemetryService(gateway)

        service.post_weather(
            WeatherDTO(
                temp=18.5,
                pressure=1008.2,
                light=123.0,
                winds=2.7,
                winddir="SW",
                rain=0.0,
                humidity=150.0,
                time=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )

        self.assertEqual(gateway.calls, [])

    def test_post_ossd_maps_payload_and_endpoint(self) -> None:
        gateway = FakeGateway()
        service = TestTelemetryService(gateway)

        service.post_ossd(
            OSSDEntryDTO(
                time=datetime(2026, 1, 1, tzinfo=UTC),
                lichtgitterNr=1,
                ossdNr=2,
                ossdStatus="E",
            )
        )

        endpoint, options = gateway.calls[0]
        self.assertEqual(endpoint, API_ENDPOINTS["OSSD_CREATE"])
        payload = options["body"]
        self.assertEqual(payload["ossdStatus"], "E")
        self.assertEqual(payload["ossdNr"], 2)

    def test_post_runtime_state_maps_payload_and_endpoint(self) -> None:
        gateway = FakeGateway()
        service = TestTelemetryService(gateway)

        service.post_witterungsstation_py_state(
            WitterungsstationPyStateDTO(
                time=datetime(2026, 1, 1, tzinfo=UTC),
                state="stop",
            )
        )

        endpoint, options = gateway.calls[0]
        self.assertEqual(endpoint, API_ENDPOINTS["WITTERUNGSSTATION_PY_STATE_CREATE"])
        payload = options["body"]
        self.assertEqual(payload["state"], "stop")


if __name__ == "__main__":
    unittest.main()
