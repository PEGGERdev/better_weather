from __future__ import annotations

from datetime import UTC, datetime

from model.ports import ClockPort


class SystemClock(ClockPort):
    def now(self) -> datetime:
        return datetime.now(UTC)
