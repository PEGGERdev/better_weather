from __future__ import annotations

import unittest

from model.api_gateway import ApiGateway
from model.api_registry import API_ENDPOINTS, get_api_endpoint_bindings


class FakeApiClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, object]] = []

    def get(self, path: str, *, timeout: float = 5.0):
        self.calls.append(("GET", path, {"timeout": timeout}))
        return {"ok": True, "method": "GET", "path": path}

    def post(self, path: str, *, json_body, timeout: float = 5.0):
        self.calls.append(("POST", path, {"body": json_body, "timeout": timeout}))
        return {"ok": True, "method": "POST", "path": path}


class TestApiGateway(ApiGateway):
    pass


class ApiGatewayEndpointTests(unittest.TestCase):
    def test_dispatches_every_registered_endpoint(self) -> None:
        api_client = FakeApiClient()
        gateway = TestApiGateway(api_client)

        for key, binding in get_api_endpoint_bindings():
            if binding.method == "GET":
                out = gateway.request(key, limit=5)
                self.assertEqual(out["method"], "GET")
            elif binding.method == "POST":
                out = gateway.request(key, body={"k": "v"})
                self.assertEqual(out["method"], "POST")

        call_map = {f"{method}:{path.split('?')[0]}": payload for method, path, payload in api_client.calls}
        self.assertIn("GET:/weather/", call_map)
        self.assertIn("GET:/ossd/", call_map)
        self.assertIn("GET:/witterungsstation_py_state/", call_map)
        self.assertIn("POST:/weather/", call_map)
        self.assertIn("POST:/ossd/", call_map)
        self.assertIn("POST:/witterungsstation_py_state/", call_map)

    def test_limit_query_is_added_for_get(self) -> None:
        api_client = FakeApiClient()
        gateway = TestApiGateway(api_client)

        gateway.request(API_ENDPOINTS["WEATHER_LIST"], limit=10)

        method, path, _payload = api_client.calls[-1]
        self.assertEqual(method, "GET")
        self.assertIn("limit=10", path)


if __name__ == "__main__":
    unittest.main()
