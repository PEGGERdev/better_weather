# model/dto.py
from __future__ import annotations

"""
Witterungstester – DTOs

Role
- Transport objects between layers (Controller <-> DbClient <-> Backend).

Conventions
- WeatherDTO.time is the measurement timestamp (datetime).
- OSSDEntryDTO.ossdStatus:
  - "O" = OK (closed/ok)
  - "E" = Error (interrupted)
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys
from typing import Literal, Optional

try:
    from shared.mongo_entity import mongo_entity
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from shared.mongo_entity import mongo_entity


@dataclass
class WeatherDTO:
    temp: Optional[float]
    pressure: Optional[float]
    light: Optional[float]
    winds: Optional[float]
    winddir: Optional[str]
    rain: Optional[float]
    humidity: Optional[float]
    time: datetime


@dataclass
class OSSDEntryDTO:
    time: datetime
    lichtgitterNr: int  # 1 or 2
    ossdNr: int         # 1 or 2
    ossdStatus: str     # "O"=OK, "E"=Error


@dataclass
class OSSDWriteResult:
    posted: int
    skipped: int


@mongo_entity(collection="witterungsstation_py_state", tags=["WitterungsstationPyState"])
@dataclass
class WitterungsstationPyStateDTO:
    time: datetime
    state: Literal["start", "stop"]
