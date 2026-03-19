from __future__ import annotations

"""
Witterungstester – DbClient (Facade)

Role
- Keeps the old DbClient API stable for existing controller code.
- Delegates API transport/endpoint selection/payload mapping to generic components.

Architecture
- ApiClient     : low-level HTTP transport
- ApiGateway    : endpoint-key based request dispatch
- TelemetryService: domain operations for weather + OSSD
"""

from typing import List, Optional

from model.api_client import ApiClient
from model.api_gateway import ApiGateway
from model.dto import OSSDEntryDTO, WeatherDTO, WitterungsstationPyStateDTO
from model.telemetry_service import TelemetryService


class DbClient:
    """Backward-compatible facade used by the app controller."""

    def __init__(
        self,
        base_url: str,
        log=None,
        *,
        telemetry_service: Optional[TelemetryService] = None,
        api_gateway: Optional[ApiGateway] = None,
        api_client: Optional[ApiClient] = None,
    ) -> None:
        self.base = base_url.rstrip("/")
        self._log = log or (lambda *a, **k: None)

        if telemetry_service is not None:
            self._telemetry = telemetry_service
            return

        resolved_api_client = api_client or ApiClient(base_url=self.base)
        resolved_api_gateway = api_gateway or ApiGateway(api_client=resolved_api_client)
        self._telemetry = TelemetryService(api_gateway=resolved_api_gateway, log=self._log)

    def post_weather(self, weather: WeatherDTO) -> None:
        self._telemetry.post_weather(weather)

    def get_weather(self, limit: Optional[int] = None) -> List[dict]:
        return self._telemetry.get_weather(limit=limit)

    def post_ossd(self, entry: OSSDEntryDTO) -> None:
        self._telemetry.post_ossd(entry)

    def get_ossd(self, limit: Optional[int] = None) -> List[dict]:
        return self._telemetry.get_ossd(limit=limit)

    def get_ossd_recent(self, limit: int = 400) -> List[dict]:
        return self.get_ossd(limit=limit)

    def post_witterungsstation_py_state(self, entry: WitterungsstationPyStateDTO) -> None:
        self._telemetry.post_witterungsstation_py_state(entry)

    def get_witterungsstation_py_state(self, limit: Optional[int] = None) -> List[dict]:
        return self._telemetry.get_witterungsstation_py_state(limit=limit)
