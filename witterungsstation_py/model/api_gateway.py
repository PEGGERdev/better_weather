from __future__ import annotations

from typing import Any, Optional

from model.api_paths import append_query_params
from model.api_registry import get_api_endpoint_binding
from model.ports import ApiClientPort


class ApiGateway:
    def __init__(self, api_client: ApiClientPort) -> None:
        self._api = api_client

    def request(self, endpoint_key: str, *, body: Any = None, limit: Optional[int] = None, timeout: float = 5.0) -> Any:
        binding = get_api_endpoint_binding(endpoint_key)
        path = binding.path
        if limit is not None and int(limit) > 0:
            path = append_query_params(path, limit=int(limit))

        if binding.method == "GET":
            return self._api.get(path, timeout=timeout)
        if binding.method == "POST":
            return self._api.post(path, json_body=body or {}, timeout=timeout)

        raise ValueError(f"Unsupported API method: {binding.method}")
