# model/ports.py
from __future__ import annotations

"""
Witterungstester – Ports (Abstractions)

Role
- Defines small, testable interfaces (Dependency Inversion / SOLID).

Concept
- The controller depends on ports (Clock/OSSD/Weather), not on concrete implementations (Serial/HID).
"""

from typing import Protocol, Optional, Tuple
from datetime import datetime


class ClockPort(Protocol):
    def now(self) -> datetime: ...


class WeatherSensorPort(Protocol):
    def read_weather(self) -> Optional[object]: ...


class OSSDPort(Protocol):
    def read_state(self) -> Optional[Tuple[bool, bool, bool, bool]]: ...
