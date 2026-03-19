from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
import unittest

from controller.backend_sync import BackendSync
from model.dto import WeatherDTO


class FakeView:
    def __init__(self) -> None:
        self.logs: list[str] = []
        self.weather_updates: list[dict] = []
        self.ossd_updates: list[tuple] = []
        self.chart_events: list[tuple] = []
        self.redraws = 0

    def append_log(self, line: str) -> None:
        self.logs.append(line)

    def update_weather(self, payload: dict) -> None:
        self.weather_updates.append(payload)

    def update_ossd(self, state: tuple) -> None:
        self.ossd_updates.append(state)

    def chart_add_ossd(self, idx: int, ts, label: str) -> None:
        self.chart_events.append((idx, label))

    def chart_redraw(self) -> None:
        self.redraws += 1


class FakeTelemetry:
    def __init__(self) -> None:
        self.posted_weather = 0
        self.ossd_rows = [{"_id": {"$oid": "abc"}, "lichtgitterNr": 1, "ossdNr": 2, "ossdStatus": "O", "time": {"$date": "2026-01-01T00:00:00Z"}}]

    def post_weather(self, _dto) -> None:
        self.posted_weather += 1

    def get_ossd_recent(self, limit=300):
        return self.ossd_rows


class FakeReader:
    def read(self):
        return {
            "temp": 20.0,
            "pressure": 1000.0,
            "light": 100.0,
            "winds": 1.0,
            "winddir": "N",
            "rain": 0.0,
            "humidity": 50.0,
            "time": datetime(2026, 1, 1, tzinfo=UTC),
        }


class BackendSyncTests(unittest.TestCase):
    def test_poll_updates_live_weather_and_backend_events(self) -> None:
        view = FakeView()
        telemetry = FakeTelemetry()
        sync = BackendSync(
            view=view,
            model_db=cast(Any, telemetry),
            post=lambda fn: fn(),
            weather_live_reader=cast(Any, FakeReader()),
            backend_interval_sec=0.0,
        )

        sync.reset_poll_schedule()
        sync.poll(has_local_ossd_events=False)

        self.assertEqual(len(view.weather_updates), 1)
        self.assertEqual(telemetry.posted_weather, 1)
        self.assertEqual(view.ossd_updates[-1], (False, True, False, False))
        self.assertEqual(len(view.chart_events), 1)

    def test_poll_posts_latest_local_weather_only_once_per_sample(self) -> None:
        view = FakeView()
        telemetry = FakeTelemetry()
        sync = BackendSync(
            view=view,
            model_db=cast(Any, telemetry),
            post=lambda fn: fn(),
            backend_interval_sec=0.0,
        )

        sample = WeatherDTO(
            temp=20.0,
            pressure=1000.0,
            light=100.0,
            winds=1.0,
            winddir="N",
            rain=0.0,
            humidity=50.0,
            time=datetime(2026, 1, 1, tzinfo=UTC),
        )

        sync.reset_poll_schedule()
        sync.poll(has_local_ossd_events=False, latest_local_weather=sample)
        sync.reset_poll_schedule()
        sync.poll(has_local_ossd_events=False, latest_local_weather=sample)

        self.assertEqual(telemetry.posted_weather, 1)

    def test_poll_does_not_override_ossd_from_backend_when_backend_sync_disabled(self) -> None:
        view = FakeView()
        telemetry = FakeTelemetry()
        sync = BackendSync(
            view=view,
            model_db=cast(Any, telemetry),
            post=lambda fn: fn(),
            backend_interval_sec=0.0,
            sync_backend_ossd=False,
        )

        sync.reset_poll_schedule()
        sync.poll(has_local_ossd_events=False)

        self.assertEqual(view.ossd_updates, [])
        self.assertEqual(view.chart_events, [])


if __name__ == "__main__":
    unittest.main()
