from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiEndpointBinding:
    method: str
    path: str


API_ENDPOINTS = {
    "WEATHER_CREATE": "WEATHER_CREATE",
    "WEATHER_LIST": "WEATHER_LIST",
    "OSSD_CREATE": "OSSD_CREATE",
    "OSSD_LIST": "OSSD_LIST",
    "WITTERUNGSSTATION_PY_STATE_CREATE": "WITTERUNGSSTATION_PY_STATE_CREATE",
    "WITTERUNGSSTATION_PY_STATE_LIST": "WITTERUNGSSTATION_PY_STATE_LIST",
}


_REGISTRY: dict[str, ApiEndpointBinding] = {
    API_ENDPOINTS["WEATHER_CREATE"]: ApiEndpointBinding(method="POST", path="/weather/"),
    API_ENDPOINTS["WEATHER_LIST"]: ApiEndpointBinding(method="GET", path="/weather/"),
    API_ENDPOINTS["OSSD_CREATE"]: ApiEndpointBinding(method="POST", path="/ossd/"),
    API_ENDPOINTS["OSSD_LIST"]: ApiEndpointBinding(method="GET", path="/ossd/"),
    API_ENDPOINTS["WITTERUNGSSTATION_PY_STATE_CREATE"]: ApiEndpointBinding(method="POST", path="/witterungsstation_py_state/"),
    API_ENDPOINTS["WITTERUNGSSTATION_PY_STATE_LIST"]: ApiEndpointBinding(method="GET", path="/witterungsstation_py_state/"),
}


def get_api_endpoint_binding(key: str) -> ApiEndpointBinding:
    binding = _REGISTRY.get(str(key or ""))
    if binding is None:
        raise KeyError(f"Unknown API endpoint key: {key}")
    return binding


def get_api_endpoint_bindings() -> list[tuple[str, ApiEndpointBinding]]:
    return sorted(_REGISTRY.items(), key=lambda item: item[0])
