from __future__ import annotations

import importlib.util
import unittest


def _deps_available() -> bool:
    return all(
        importlib.util.find_spec(name) is not None
        for name in ("bson", "fastapi")
    )


@unittest.skipUnless(_deps_available(), "backend routing deps are not installed")
class RoutingHelperTests(unittest.TestCase):
    def test_parse_object_id_rejects_invalid_value(self) -> None:
        from fastapi import HTTPException

        from routing.object_id import parse_object_id

        with self.assertRaises(HTTPException) as ctx:
            parse_object_id("invalid-id")

        self.assertEqual(ctx.exception.status_code, 400)

    def test_map_http_errors_wraps_unhandled_exceptions(self) -> None:
        from fastapi import HTTPException

        from routing.error_mapper import map_http_errors

        @map_http_errors
        async def boom():
            raise RuntimeError("bad")

        with self.assertRaises(HTTPException) as ctx:
            import asyncio

            asyncio.run(boom())

        self.assertEqual(ctx.exception.status_code, 500)
        self.assertEqual(ctx.exception.detail["error"], "bad")
