from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

@dataclass
class WeatherDTO:
    temp: Optional[float]
    preassure: Optional[float]
    light: Optional[float]
    winds: Optional[float]
    winddir: Optional[str]
    rain: Optional[float]
    humidity: Optional[float]
    time: datetime

@dataclass
class OSSDEntryDTO:
    time: datetime
    lichtgitterNr: int  # 1 oder 2
    ossdNr: int         # 1 oder 2
    ossdStatus: str     # "O"=OK, "E"=Error

@dataclass
class OSSDWriteResult:
    posted: int
    skipped: int
