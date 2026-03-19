from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional, Protocol, Tuple


class BaseOutputHandler(ABC):
    @abstractmethod
    def emit_ossd(
        self,
        ts: datetime,
        lichtgitter_nr: int,
        ossd_nr: int,
        status: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def emit_weather(
        self,
        ts: datetime,
        temp: float,
        pressure: float,
        humidity: float,
        winds: float,
        winddir: str,
        rain: float,
        light: float,
    ) -> None:
        raise NotImplementedError

    def close(self) -> None:
        return None


class BaseOssdReader(ABC):
    @abstractmethod
    def read(self) -> Optional[Tuple[bool, bool, bool, bool]]:
        raise NotImplementedError


class BaseWeatherReader(ABC):
    @abstractmethod
    def read(self) -> Optional[dict[str, Any]]:
        raise NotImplementedError


class BaseLifecycleService(ABC):
    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class LogPort(Protocol):
    def __call__(self, message: str) -> None: ...
