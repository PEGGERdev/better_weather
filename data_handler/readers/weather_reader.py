from __future__ import annotations

from typing import Any, Callable, Optional

from data_handler.registry import register_service
from shared.hid_client import HidClient
from shared.parsers import WeatherParser


@register_service(kind="reader", name="weather")
class WeatherReader:
    MAX_ATTEMPTS = 3

    def __init__(self, hid_client: HidClient, parser: WeatherParser, log: Callable[[str], None]) -> None:
        self._hid = hid_client
        self._parser = parser
        self._log = log

    def read(self) -> Optional[dict[str, Any]]:
        for attempt in range(self.MAX_ATTEMPTS):
            ptr = self._hid.query("A1 00 1E 20 A1 00 1E 20", 32, timeout=0.6)
            if not ptr:
                continue

            tried_swaps = [self._parser._ptr_swap, not self._parser._ptr_swap]
            for swap in tried_swaps:
                p_lo, p_hi = WeatherParser.get_pointer_bytes(ptr, swap)
                cmd = " ".join(f"{x:02X}" for x in [0xA1, p_hi, p_lo, 0x20, 0xA1, p_hi, p_lo, 0x20])
                raw = self._hid.query(cmd, 32, timeout=1.2)
                if not raw:
                    continue

                payload = self._parser.parse_with_calibration(raw)
                if payload and WeatherParser.is_sane_payload(payload):
                    return payload

                if payload and attempt == self.MAX_ATTEMPTS - 1:
                    issues = WeatherParser.sanity_issues(payload)
                    self._log(
                        "WeatherReader: rejected weather sample "
                        f"({', '.join(issues)}) payload={payload}"
                    )

            if attempt == self.MAX_ATTEMPTS - 1:
                self._log("WeatherReader: no sane weather sample after retries")

        return None
