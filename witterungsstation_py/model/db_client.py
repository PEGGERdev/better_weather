from __future__ import annotations
import requests
from typing import Iterable, List, Tuple, Optional
from datetime import datetime

from model.dto import WeatherDTO, OSSDEntryDTO

class DbClient:
    """Kommuniziert mit dem FastAPI-Backend (keine direkte DB)."""
    def __init__(self, base_url: str, log=None) -> None:
        self.base = base_url.rstrip("/")
        self._log = log or (lambda *a, **k: None)
        self._s = requests.Session()
        self._s.headers.update({"Content-Type": "application/json"})

    # ----- Weather -----
    def post_weather(self, w: WeatherDTO) -> None:
        try:
            self._s.post(f"{self.base}/weather/", json=w.__dict__, timeout=5)
        except Exception as e:
            self._log(f"POST /weather fehlgeschlagen: {e}")

    # ----- OSSD -----
    def post_ossd(self, entry: OSSDEntryDTO) -> None:
        self._s.post(f"{self.base}/ossd/", json={
            "time": entry.time.isoformat(),
            "lichtgitterNr": entry.lichtgitterNr,
            "ossdNr": entry.ossdNr,
            "ossdStatus": entry.ossdStatus
        }, timeout=5)

    def get_ossd_recent(self, limit: int = 200) -> List[dict]:
        """Holt alle und schneidet hinten ab – Router hat kein Limit/Sort."""
        r = self._s.get(f"{self.base}/ossd/", timeout=5)
        r.raise_for_status()
        data = r.json()
        # simple tail
        if isinstance(data, list) and len(data) > limit:
            data = data[-limit:]
        return data
