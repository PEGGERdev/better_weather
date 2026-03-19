from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.hid_client import HidClient, HidConfig
from shared.parsers import WeatherParser


class LiveWeatherReader:
    """Direct weather-station reader for instant GUI updates only."""

    MAX_ATTEMPTS = 3

    def __init__(
        self,
        *,
        vid: int,
        pid: int,
        report_size: int = 32,
        log: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._log = log or (lambda _msg: None)
        self._hid = HidClient(HidConfig(vid=vid, pid=pid, report_size=report_size), log=self._log)
        self._parser = WeatherParser(log=self._log)
        self._opened = False

    def open(self) -> bool:
        if self._opened and self._hid.is_open():
            return True
        self._opened = self._hid.open()
        return self._opened

    def close(self) -> None:
        self._hid.close()
        self._opened = False

    def read(self) -> Optional[dict]:
        if not self._hid.is_open() and not self.open():
            return None

        for _attempt in range(self.MAX_ATTEMPTS):
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

        return None
