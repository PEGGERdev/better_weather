from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
import unittest

from controller.local_ossd_relay import LocalOssdRelay
from model.dto import OSSDEntryDTO


class FakeView:
    def __init__(self) -> None:
        self.ossd_updates: list[tuple] = []
        self.chart_events: list[tuple] = []
        self.redraws = 0

    def update_ossd(self, state: tuple) -> None:
        self.ossd_updates.append(state)

    def chart_add_ossd(self, idx: int, ts, label: str) -> None:
        self.chart_events.append((idx, label))

    def chart_redraw(self) -> None:
        self.redraws += 1


class FakeHandler:
    def drain_ossd_events(self):
        return [OSSDEntryDTO(time=datetime(2026, 1, 1, tzinfo=UTC), lichtgitterNr=2, ossdNr=1, ossdStatus="O")]


class LocalOssdRelayTests(unittest.TestCase):
    def test_apply_posts_events_and_updates_view(self) -> None:
        view = FakeView()
        relay = LocalOssdRelay(
            data_handler=cast(Any, FakeHandler()),
            view=view,
            post=lambda fn: fn(),
        )

        used = relay.apply()

        self.assertTrue(used)
        self.assertEqual(view.ossd_updates[-1], (False, False, True, False))
        self.assertEqual(view.chart_events[-1], (2, "LG2 OSSD1"))
        self.assertEqual(view.redraws, 1)


if __name__ == "__main__":
    unittest.main()
