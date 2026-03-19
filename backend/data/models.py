from datetime import UTC, datetime
from pathlib import Path
import re
import sys
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

try:
    from shared.mongo_entity import mongo_entity
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from shared.mongo_entity import mongo_entity


@mongo_entity(collection="weather", tags=["Weather"])
class Weather(BaseModel):
    temp: float = Field(ge=-80.0, le=80.0)
    pressure: float = Field(ge=850.0, le=1200.0)
    light: float = Field(ge=0.0)
    winds: float = Field(ge=0.0, le=120.0)
    winddir: str = Field(min_length=1, max_length=3)
    rain: float = Field(ge=0.0)
    humidity: float = Field(ge=0.0, le=100.0)
    time: Optional[datetime] = None

    @field_validator("time")
    @classmethod
    def default_now(cls, value: datetime | None) -> datetime:
        return value or datetime.now(UTC)

    @field_validator("winddir")
    @classmethod
    def uppercase_and_validate(cls, value: str) -> str:
        normalized = value.upper()
        if not re.fullmatch(r"[A-Z]{1,3}", normalized):
            raise ValueError("winddir must be 1-3 letters (e.g., N, NE, SSW)")
        return normalized


@mongo_entity(collection="ossd", tags=["OSSD"])
class OSSD(BaseModel):
    time: Optional[datetime] = None
    lichtgitterNr: int = Field(ge=1, le=2)
    ossdNr: int = Field(ge=1, le=2)
    ossdStatus: Literal["O", "E"]

    @field_validator("time")
    @classmethod
    def default_now(cls, value: datetime | None) -> datetime:
        return value or datetime.now(UTC)

    @field_validator("ossdStatus", mode="before")
    @classmethod
    def normalize_ossd_status(cls, value: object) -> object:
        text = str(value or "").strip().upper()
        if text in {"O", "E"}:
            return text
        return value


@mongo_entity(collection="witterungsstation_py_state", tags=["WitterungsstationPyState"])
class WitterungsstationPyState(BaseModel):
    time: Optional[datetime] = None
    state: Literal["start", "stop"]

    @field_validator("time")
    @classmethod
    def default_now(cls, value: datetime | None) -> datetime:
        return value or datetime.now(UTC)

    @field_validator("state", mode="before")
    @classmethod
    def normalize_state(cls, value: object) -> object:
        text = str(value or "").strip().lower()
        if text in {"start", "stop"}:
            return text
        return value
