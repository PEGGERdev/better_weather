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
from typing import Any

from model.dto import OSSDEntryDTO, WeatherDTO, WitterungsstationPyStateDTO


class ClockPort(Protocol):
    def now(self) -> datetime: ...


class WeatherSensorPort(Protocol):
    def read_weather(self) -> Optional[object]: ...


class OSSDPort(Protocol):
    def read_state(self) -> Optional[Tuple[bool, bool, bool, bool]]: ...


class TelemetryPort(Protocol):
    def post_weather(self, weather: WeatherDTO) -> None: ...
    def get_weather(self, limit: Optional[int] = None) -> list[dict]: ...
    def post_ossd(self, entry: OSSDEntryDTO) -> None: ...
    def get_ossd(self, limit: Optional[int] = None) -> list[dict]: ...
    def get_ossd_recent(self, limit: int = 400) -> list[dict]: ...
    def post_witterungsstation_py_state(self, entry: WitterungsstationPyStateDTO) -> None: ...
    def get_witterungsstation_py_state(self, limit: Optional[int] = None) -> list[dict]: ...


class ApiClientPort(Protocol):
    def get(self, path: str, *, timeout: float = 5.0) -> Any: ...
    def post(self, path: str, *, json_body: Any, timeout: float = 5.0) -> Any: ...


class ApiGatewayPort(Protocol):
    def request(self, endpoint_key: str, *, body: Any = None, limit: Optional[int] = None, timeout: float = 5.0) -> Any: ...
