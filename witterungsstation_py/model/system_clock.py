# model/system_clock.py
from __future__ import annotations

"""
Witterungstester – SystemClock

Role
- Time source implementation for ClockPort (swap-able for testing).
"""

from datetime import datetime


class SystemClock:
    def now(self) -> datetime:
        return datetime.now()
