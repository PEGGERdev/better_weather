from __future__ import annotations

import os
import time
from pathlib import Path
from typing import List, Optional

from model.api_registry import API_ENDPOINTS
from model.base_service import BaseService
from model.dto import OSSDEntryDTO, WeatherDTO, WitterungsstationPyStateDTO
from model.jsonl_queue import JsonlQueue
from model.ports import ApiGatewayPort
from model.payload_mapper import ossd_to_payload, weather_to_payload, witterungsstation_py_state_to_payload


class TelemetryService(BaseService):
    def __init__(self, api_gateway: ApiGatewayPort, log=None) -> None:
        super().__init__(service_name="telemetry")
        self._api = api_gateway
        self._log = log or (lambda *a, **k: None)
        self._backend_down_last_log = 0.0
        self._wal_path = Path(
            os.getenv(
                "TELEMETRY_WAL_PATH",
                str(Path(__file__).resolve().parents[2] / "telemetry_wal.jsonl"),
            )
        )
        self._queue = JsonlQueue(self._wal_path, on_error=self._log)

    @staticmethod
    def _is_backend_unreachable(error: Exception) -> bool:
        text = str(error).lower()
        markers = (
            "connection refused",
            "failed to establish a new connection",
            "max retries exceeded",
            "name or service not known",
            "temporary failure in name resolution",
            "timed out",
        )
        return any(marker in text for marker in markers)

    def _log_backend_unreachable(self) -> None:
        now = time.monotonic()
        if now - self._backend_down_last_log < 10.0:
            return
        self._backend_down_last_log = now
        self._log("Backend not reachable. Telemetry events are queued and will be retried.")

    def _load_queue(self) -> list[dict]:
        return self._queue.load()

    def _save_queue(self, items: list[dict]) -> None:
        self._queue.save(items)

    def _enqueue(self, endpoint_key: str, payload: dict) -> None:
        self._queue.append({"endpoint": endpoint_key, "payload": payload})

    def _flush_queue(self) -> None:
        pending = self._load_queue()
        if not pending:
            return

        while pending:
            item = pending[0]
            endpoint = str(item.get("endpoint") or "")
            payload = item.get("payload")
            if not endpoint or not isinstance(payload, dict):
                pending.pop(0)
                continue
            try:
                self._api.request(endpoint, body=payload)
            except Exception as error:
                if self._is_backend_unreachable(error):
                    self._log_backend_unreachable()
                    break
                self.capture_error(error, f"Replay failed for {endpoint}")
                self._log(f"Replay failed for {endpoint}: {error}")
                pending.pop(0)
                continue
            pending.pop(0)

        self._save_queue(pending)

    def _safe_post(self, endpoint: str, payload: dict, label: str) -> None:
        self._flush_queue()
        try:
            self._api.request(endpoint, body=payload)
            self.clear_error()
        except Exception as error:
            if self._is_backend_unreachable(error):
                self._enqueue(endpoint, payload)
                self._log_backend_unreachable()
                return
            self.capture_error(error, f"POST {label} failed")
            self._log(f"POST {label} failed: {error}")

    def post_weather(self, weather: WeatherDTO) -> None:
        payload = weather_to_payload(weather)
        if payload is None:
            self._log("POST /weather skipped: invalid weather payload")
            return
        self._safe_post(API_ENDPOINTS["WEATHER_CREATE"], payload, "/weather")

    def get_weather(self, limit: Optional[int] = None) -> List[dict]:
        self._flush_queue()
        try:
            data = self._api.request(API_ENDPOINTS["WEATHER_LIST"], limit=limit)
            self.clear_error()
            return data if isinstance(data, list) else []
        except Exception as error:
            if self._is_backend_unreachable(error):
                self._log_backend_unreachable()
                return []
            self.capture_error(error, "GET /weather failed")
            self._log(f"GET /weather failed: {error}")
            return []

    def post_ossd(self, entry: OSSDEntryDTO) -> None:
        payload = ossd_to_payload(entry)
        if payload is None:
            self._log("POST /ossd skipped: invalid OSSD payload")
            return
        self._safe_post(API_ENDPOINTS["OSSD_CREATE"], payload, "/ossd")

    def get_ossd(self, limit: Optional[int] = None) -> List[dict]:
        self._flush_queue()
        try:
            data = self._api.request(API_ENDPOINTS["OSSD_LIST"], limit=limit)
            self.clear_error()
            return data if isinstance(data, list) else []
        except Exception as error:
            if self._is_backend_unreachable(error):
                self._log_backend_unreachable()
                return []
            self.capture_error(error, "GET /ossd failed")
            self._log(f"GET /ossd failed: {error}")
            return []

    def post_witterungsstation_py_state(self, entry: WitterungsstationPyStateDTO) -> None:
        payload = witterungsstation_py_state_to_payload(entry)
        if payload is None:
            self._log("POST /witterungsstation_py_state skipped: invalid state payload")
            return
        self._safe_post(API_ENDPOINTS["WITTERUNGSSTATION_PY_STATE_CREATE"], payload, "/witterungsstation_py_state")

    def get_witterungsstation_py_state(self, limit: Optional[int] = None) -> List[dict]:
        self._flush_queue()
        try:
            data = self._api.request(API_ENDPOINTS["WITTERUNGSSTATION_PY_STATE_LIST"], limit=limit)
            self.clear_error()
            return data if isinstance(data, list) else []
        except Exception as error:
            if self._is_backend_unreachable(error):
                self._log_backend_unreachable()
                return []
            self.capture_error(error, "GET /witterungsstation_py_state failed")
            self._log(f"GET /witterungsstation_py_state failed: {error}")
            return []
