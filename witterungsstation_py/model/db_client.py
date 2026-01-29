from __future__ import annotations

"""
Witterungstester – DbClient (HTTP Gateway)

Role
- Wraps HTTP communication to the FastAPI backend (no direct DB access).

Error semantics
- Weather POST: best-effort (logs failures, does not raise)
- OSSD POST   : strict (raises on non-2xx), so controller can keep backlog/WAL consistent

WHY strict OSSD?
- requests.post() does not raise on HTTP 4xx/5xx by default.
- Without raise_for_status(), failed writes could be treated as success and dropped from WAL.
"""

import requests
from typing import List
from model.dto import WeatherDTO, OSSDEntryDTO

from exception_handler import format_current_exception


class DbClient:
    """Communicates with the FastAPI backend (no direct DB)."""

    def __init__(self, base_url: str, log=None) -> None:
        self.base = base_url.rstrip("/")
        self._log = log or (lambda *a, **k: None)
        self._s = requests.Session()
        self._s.headers.update({"Content-Type": "application/json"})

    # ---------------- Weather (best-effort) ----------------
    def post_weather(self, w: WeatherDTO) -> None:
        """
        POST /weather (best-effort)

        NOTE
        - Logs network errors and HTTP non-2xx responses.
        - Does not raise: weather can be dropped when backend is temporarily unavailable.
        """
        try:
            r = self._s.post(f"{self.base}/weather/", json=w.__dict__, timeout=5)
            if not r.ok:
                self._log(format_current_exception(f"POST /weather returned HTTP {r.status_code}: {r.text}"))
        except Exception as e:
            self._log(format_current_exception(f"POST /weather failed: {e}"))
        
    def get_weather(self, limit: int = None) -> WeatherDTO:
        """
        GET /weather and return a tail slice if limit is given.

        NOTE
        - If the backend does not provide server-side limit/sort, we take a client-side tail.
        """

        r = self._s.get(f"{self.base}/weather/", timeout=5)
        r.raise_for_status()
        data = r.json()
        def limited_data(data, limit):
            if isinstance(data, list) and len(data) > limit:
                return data[-limit:]
        return data if (limit == None) else limited_data(data, limit)

    # ---------------- OSSD (strict) ----------------
    def post_ossd(self, entry: OSSDEntryDTO) -> None:
        """
        POST /ossd (strict)

        WHY
        - OSSD events must not be silently lost.
        - Non-2xx must raise so the controller keeps backlog + WAL.
        """
        r = self._s.post(
            f"{self.base}/ossd/",
            json={
                "time": None,
                "lichtgitterNr": entry.lichtgitterNr,
                "ossdNr": entry.ossdNr,
                "ossdStatus": entry.ossdStatus,
            },
            timeout=5,
        )
        r.raise_for_status()

    def get_ossd(self, limit: int = None) -> List[dict]:
        """
        GET /ossd and return a tail slice if limit is given.

        NOTE
        - If the backend does not provide server-side limit/sort, we take a client-side tail.
        """
        r = self._s.get(f"{self.base}/ossd/", timeout=5)
        r.raise_for_status()
        data = r.json()
        def limited_data(data, limit):
            if isinstance(data, list) and len(data) > limit:
                return data[-limit:]
        return data if (limit == None) else limited_data(data, limit)
