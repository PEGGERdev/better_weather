from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

import requests

from model.api_paths import path_variants


@dataclass
class ApiError(Exception):
    status: int
    method: str
    path: str
    data: Any

    def __str__(self) -> str:
        return f"HTTP {self.status} {self.method} {self.path}".strip()


class ApiClient:
    def __init__(self, base_url: str, session: Optional[requests.Session] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = session or requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    @staticmethod
    def _parse_payload(response: requests.Response) -> Any:
        text = response.text or ""
        if not text:
            return {}
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        timeout: float = 5.0,
    ) -> Any:
        m = str(method or "GET").upper()
        last_error: Exception | None = None

        for variant in path_variants(path):
            url = f"{self.base_url}{variant}"
            try:
                response = self._session.request(m, url, json=json_body, timeout=timeout)
                payload = self._parse_payload(response)
                if not response.ok:
                    raise ApiError(
                        status=int(response.status_code),
                        method=m,
                        path=variant,
                        data=payload,
                    )
                return payload
            except ApiError as error:
                last_error = error
                if error.status != 404:
                    raise
            except Exception as error:
                last_error = error
                raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Unknown API error")

    def get(self, path: str, *, timeout: float = 5.0) -> Any:
        return self.request("GET", path, timeout=timeout)

    def post(self, path: str, *, json_body: Any, timeout: float = 5.0) -> Any:
        return self.request("POST", path, json_body=json_body, timeout=timeout)
