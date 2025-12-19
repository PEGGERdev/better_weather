from __future__ import annotations
from typing import Protocol, Optional, Tuple
from datetime import datetime

class ClockPort(Protocol):
    def now(self) -> datetime: ...

class WeatherSensorPort(Protocol):
    def read_weather(self) -> Optional[object]: ...

class OSSDPort(Protocol):
    def read_state(self) -> Optional[Tuple[bool, bool, bool, bool]]: ...
