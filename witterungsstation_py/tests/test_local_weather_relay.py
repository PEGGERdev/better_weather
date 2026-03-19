from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
import unittest

from controller.local_weather_relay import LocalWeatherRelay
from model.dto import WeatherDTO


class FakeView:
    def __init__(self) -> None:
        self.weather_updates: list[dict] = []

    def update_weather(self, payload: dict) -> None:
        self.weather_updates.append(payload)


class FakeHandler:
    def drain_weather_events(self):
        return [
            WeatherDTO(
                temp=20.0,
                pressure=1000.0,
                light=100.0,
                winds=1.0,
                winddir="NE",
                rain=0.0,
                humidity=50.0,
                time=datetime(2026, 1, 1, tzinfo=UTC),
            )
        ]


class LocalWeatherRelayTests(unittest.TestCase):
    def test_apply_updates_view_from_ipc_weather(self) -> None:
        view = FakeView()
        relay = LocalWeatherRelay(
            data_handler=cast(Any, FakeHandler()),
            view=view,
            post=lambda fn: fn(),
        )

        used = relay.apply()

        self.assertTrue(used)
        self.assertEqual(len(view.weather_updates), 1)
        self.assertEqual(view.weather_updates[0]["winddir"], "NE")


if __name__ == "__main__":
    unittest.main()
