from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests

from data_handler.contracts import BaseOutputHandler
from data_handler.registry import register_service
from shared.jsonl_queue import JsonlQueue


@register_service(kind="output", name="backend")
class BackendOutputHandler(BaseOutputHandler):
    def __init__(self, base_url: str, log: Callable[[str], None]) -> None:
        self._base_url = base_url.rstrip("/")
        self._log = log
        self._wal_path = Path(
            os.getenv(
                "DATA_HANDLER_WAL_PATH",
                str(Path(__file__).resolve().parents[2] / "ossd_events_wal.jsonl"),
            )
        )
        self._queue = JsonlQueue(self._wal_path, on_error=self._log)
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def _send(self, path: str, payload: dict[str, Any]) -> bool:
        url = f"{self._base_url}{path}"
        try:
            resp = self._session.post(url, json=payload, timeout=5)
            if not resp.ok:
                self._log(f"POST {url} failed: HTTP {resp.status_code}")
                return False
            return True
        except Exception:
            self._log(f"Backend not reachable: {url}")
            return False

    def _load_backlog(self) -> list[dict[str, Any]]:
        return self._queue.load()

    def _save_backlog(self, items: list[dict[str, Any]]) -> None:
        self._queue.save(items)

    def _enqueue(self, path: str, payload: dict[str, Any]) -> None:
        self._queue.append({"path": path, "payload": payload})

    def _flush_backlog(self) -> None:
        backlog = self._load_backlog()
        if not backlog:
            return

        while backlog:
            item = backlog[0]
            path = str(item.get("path") or "")
            payload = item.get("payload")
            if not path or not isinstance(payload, dict):
                backlog.pop(0)
                continue
            if not self._send(path, payload):
                break
            backlog.pop(0)

        self._save_backlog(backlog)

    def _post(self, path: str, payload: dict[str, Any]) -> None:
        self._flush_backlog()
        if not self._send(path, payload):
            self._enqueue(path, payload)

    def emit_ossd(
        self,
        ts: datetime,
        lichtgitter_nr: int,
        ossd_nr: int,
        status: str,
    ) -> None:
        payload = {
            "time": ts.isoformat() if ts else None,
            "lichtgitterNr": lichtgitter_nr,
            "ossdNr": ossd_nr,
            "ossdStatus": status,
        }
        self._post("/ossd/", payload)

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
        payload = {
            "time": ts.isoformat() if ts else None,
            "temp": temp,
            "pressure": pressure,
            "humidity": humidity,
            "winds": winds,
            "winddir": winddir,
            "rain": rain,
            "light": light,
        }
        self._post("/weather/", payload)
