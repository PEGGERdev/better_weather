from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, cast
import unittest

from controller.live_runtime_controller import LiveRuntimeController


class FakeView:
    def __init__(self) -> None:
        self.logs: list[str] = []
        self.weather_updates: list[dict] = []
        self.ossd_updates: list[tuple] = []
        self.chart_events: list[tuple] = []
        self.running = False
        self.status = ""
        self.telemetry_mode = ""

    def set_status(self, text: str) -> None:
        self.status = text

    def set_running_state(self, running: bool) -> None:
        self.running = running

    def append_log(self, line: str) -> None:
        self.logs.append(str(line))

    def set_telemetry_mode(self, text: str) -> None:
        self.telemetry_mode = text

    def update_weather(self, payload: dict) -> None:
        self.weather_updates.append(payload)

    def update_ossd(self, st: tuple) -> None:
        self.ossd_updates.append(st)

    def chart_add_ossd(self, channel_idx: int, ts, label: str) -> None:
        self.chart_events.append((channel_idx, label))

    def chart_redraw(self) -> None:
        return None


class FakeTelemetry:
    def __init__(self) -> None:
        self.weather_calls = 0
        self.ossd_calls = 0
        self.post_weather_calls = 0
        self.post_ossd_calls = 0
        self.post_state_calls = 0
        self.weather = [
            {
                "_id": {"$oid": "w1"},
                "temp": 21.0,
                "pressure": 1007.0,
                "light": 200.0,
                "winds": 1.0,
                "winddir": "NE",
                "rain": 0.0,
                "humidity": 50.0,
                "time": {"$date": "2026-02-24T10:00:00Z"},
            }
        ]
        self.ossd = [
            {
                "_id": {"$oid": "o1"},
                "lichtgitterNr": 1,
                "ossdNr": 2,
                "ossdStatus": "E",
                "time": {"$date": "2026-02-24T10:00:00Z"},
            }
        ]

    def get_weather(self, limit=None):
        self.weather_calls += 1
        return self.weather

    def post_weather(self, _weather):
        self.post_weather_calls += 1

    def get_ossd_recent(self, limit=300):
        self.ossd_calls += 1
        return self.ossd

    def post_ossd(self, _entry):
        self.post_ossd_calls += 1
        return None

    def post_witterungsstation_py_state(self, _entry):
        self.post_state_calls += 1
        return None

    def get_ossd(self, limit=None):
        return self.ossd

    def get_witterungsstation_py_state(self, limit=None):
        return []


class FakeHandler:
    def __init__(self) -> None:
        self.running = False
        self.weather_events = []
        self.ossd_events = []

    def start(self):
        self.running = True
        return True

    def stop(self):
        self.running = False

    def is_running(self):
        return self.running

    def drain_ossd_events(self):
        events = list(self.ossd_events)
        self.ossd_events.clear()
        return events

    def drain_weather_events(self):
        events = list(self.weather_events)
        self.weather_events.clear()
        return events


class FakeLiveWeatherReader:
    def __init__(self) -> None:
        self.opened = False
        self.read_calls = 0

    def open(self):
        self.opened = True
        return True

    def close(self):
        self.opened = False

    def read(self):
        self.read_calls += 1
        return {
            "temp": 24.0,
            "pressure": 1012.0,
            "light": 10.0,
            "winds": 0.2,
            "winddir": "N",
            "rain": 0.0,
            "humidity": 55.0,
            "time": datetime(2026, 2, 24, 10, 1, tzinfo=UTC),
        }


class LiveRuntimeControllerTests(unittest.TestCase):
    def test_poll_once_updates_view_without_manual_click(self) -> None:
        view = FakeView()
        ctrl = LiveRuntimeController(
            view=view,
            model_db=cast(Any, FakeTelemetry()),
            data_handler=cast(Any, FakeHandler()),
            poll_sec=0.2,
        )

        ctrl._poll_once()

        self.assertEqual(len(view.weather_updates), 0)
        self.assertEqual(len(view.ossd_updates), 0)
        self.assertEqual(len(view.chart_events), 0)
        self.assertIn("Subprozess", view.telemetry_mode)

    def test_live_weather_updates_every_poll_while_backend_is_throttled(self) -> None:
        view = FakeView()
        telemetry = FakeTelemetry()
        live_reader = FakeLiveWeatherReader()
        ctrl = LiveRuntimeController(
            view=view,
            model_db=cast(Any, telemetry),
            data_handler=cast(Any, FakeHandler()),
            weather_live_reader=live_reader,
            poll_sec=0.2,
            backend_interval_sec=30.0,
        )

        ctrl._poll_once()
        ctrl._poll_once()

        self.assertGreaterEqual(len(view.weather_updates), 2)
        self.assertEqual(telemetry.weather_calls, 0)
        self.assertEqual(telemetry.post_weather_calls, 1)
        self.assertEqual(telemetry.ossd_calls, 0)
        self.assertIn("Fallback", view.telemetry_mode)

    def test_gui_managed_data_handler_updates_weather_and_posts_on_interval(self) -> None:
        view = FakeView()
        telemetry = FakeTelemetry()
        handler = FakeHandler()
        handler.weather_events.append(
            cast(
                Any,
                type("WeatherEvent", (), {
                    "temp": 23.0,
                    "pressure": 1005.0,
                    "light": 99.0,
                    "winds": 0.5,
                    "winddir": "NW",
                    "rain": 0.0,
                    "humidity": 60.0,
                    "time": datetime(2026, 2, 24, 10, 2, tzinfo=UTC),
                })(),
            )
        )
        ctrl = LiveRuntimeController(
            view=view,
            model_db=cast(Any, telemetry),
            data_handler=cast(Any, handler),
            weather_live_reader=None,
            poll_sec=0.2,
            backend_interval_sec=30.0,
        )

        ctrl._poll_once()

        self.assertEqual(len(view.weather_updates), 1)
        self.assertEqual(view.weather_updates[0]["winddir"], "NW")
        self.assertEqual(telemetry.post_weather_calls, 1)

    def test_gui_managed_data_handler_posts_local_ossd_to_backend(self) -> None:
        view = FakeView()
        telemetry = FakeTelemetry()
        handler = FakeHandler()
        handler.ossd_events.append(
            cast(
                Any,
                type("OssdEvent", (), {
                    "lichtgitterNr": 1,
                    "ossdNr": 2,
                    "ossdStatus": "E",
                    "time": datetime(2026, 2, 24, 10, 4, tzinfo=UTC),
                })(),
            )
        )
        ctrl = LiveRuntimeController(
            view=view,
            model_db=cast(Any, telemetry),
            data_handler=cast(Any, handler),
            weather_live_reader=None,
            poll_sec=0.2,
            backend_interval_sec=30.0,
        )

        ctrl._poll_once()

        self.assertEqual(view.chart_events[-1], (1, "LG1 OSSD2"))
        self.assertEqual(telemetry.post_ossd_calls, 1)

    def test_test_once_updates_view_and_posts_local_weather(self) -> None:
        view = FakeView()
        telemetry = FakeTelemetry()
        handler = FakeHandler()
        handler.weather_events.append(
            cast(
                Any,
                type("WeatherEvent", (), {
                    "temp": 19.5,
                    "pressure": 1008.0,
                    "light": 42.0,
                    "winds": 0.8,
                    "winddir": "S",
                    "rain": 0.1,
                    "humidity": 61.0,
                    "time": datetime(2026, 2, 24, 10, 3, tzinfo=UTC),
                })(),
            )
        )
        ctrl = LiveRuntimeController(
            view=view,
            model_db=cast(Any, telemetry),
            data_handler=cast(Any, handler),
            weather_live_reader=None,
            poll_sec=0.2,
            backend_interval_sec=30.0,
        )

        ctrl.test_once()

        self.assertEqual(len(view.weather_updates), 1)
        self.assertEqual(view.weather_updates[0]["winddir"], "S")
        self.assertEqual(telemetry.post_weather_calls, 1)

    def test_start_and_stop_publish_runtime_state_transitions(self) -> None:
        view = FakeView()
        telemetry = FakeTelemetry()
        ctrl = LiveRuntimeController(
            view=view,
            model_db=cast(Any, telemetry),
            data_handler=cast(Any, FakeHandler()),
            poll_sec=0.2,
        )

        ctrl.start()
        ctrl.start()
        ctrl.stop()
        ctrl.stop()

        self.assertEqual(telemetry.post_state_calls, 2)


if __name__ == "__main__":
    unittest.main()
