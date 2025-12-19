from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re

class Weather(BaseModel):
    """Weather reading."""
    temp: float
    preassure: float
    light: float
    winds: float
    winddir: str = Field(min_length=1, max_length=3)
    rain: float
    humidity: float
    time: Optional[datetime] = None

    @field_validator("time")
    @classmethod
    def default_now(cls, v):
        return v or datetime.now()

    @field_validator("winddir")
    @classmethod
    def uppercase_and_validate(cls, v: str) -> str:
        vv = v.upper()
        if not re.fullmatch(r"[A-Z]{1,3}", vv):
            raise ValueError("winddir must be 1-3 letters (e.g., N, NE, SSW)")
        return vv

class OSSD(BaseModel):
    """OSSD Event (without FK)."""
    time: Optional[datetime] = None
    lichtgitterNr: int
    ossdNr: int
    ossdStatus: str = Field(min_length=1, max_length=4)

    @field_validator("time")
    @classmethod
    def default_now(cls, v):
        return v or datetime.now()
