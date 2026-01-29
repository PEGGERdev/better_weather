from __future__ import annotations

"""
Witterungstester – SerialOSSD (Serial Adapter)

Role
- Talks to the Arduino via serial and returns 4 OSSD channels as Tuple[bool,bool,bool,bool].

Protocol
- Request : "G\\n"
- Response: "G0O,G1O,G2O,G3O" (O=OK, E=Error)

Error handling
- Best-effort: parse failures -> None; IO exceptions -> log + None
"""

import time
import re
from typing import Optional, Tuple, Callable
import serial

from model.ports import OSSDPort, ClockPort
from exception_handler import format_current_exception


class SerialOSSD(OSSDPort):
    """
    Reads Arduino over serial.
    Expected response to 'G\\n': 'G0O,G1O,G2O,G3O' (or ...E).
    """

    def __init__(self, port: str, baud: int, clock: ClockPort, log: Callable[[str], None] | None = None):
        self._ser = serial.Serial(port=port, baudrate=baud, timeout=1.0)
        self._clock = clock
        self._log = log or (lambda *_: None)

        # NOTE: Arduino/serial often needs a brief moment after open().

    # ---------------- parsing ----------------
    def _parse_line(self, line: str) -> Optional[Tuple[bool, bool, bool, bool]]:
        """
        Parses "G0O,G1O,G2O,G3O" or "G0E,...".

        NOTE
        - We expect exactly 4 matches (G0..G3). Anything else is incomplete/noise.
        """
        m = re.findall(r"G([0-3])([OE])", line)
        if len(m) != 4:
            return None
        vals = [None, None, None, None]
        for idx, ch in m:
            vals[int(idx)] = (ch == "O")  # O=OK -> True
        if any(v is None for v in vals):
            return None
        return tuple(bool(v) for v in vals)  # type: ignore

    # ---------------- OSSDPort ----------------
    def read_state(self) -> Optional[Tuple[bool, bool, bool, bool]]:
        try:
            self._ser.reset_input_buffer()
            self._ser.write(b"G\n")
            self._ser.flush()
            line = self._ser.readline().decode(errors="ignore").strip()
            st = self._parse_line(line)
            if st is None:
                # NOTE: sometimes an unrelated line arrives first -> retry once.
                time.sleep(0.05)
                line2 = self._ser.readline().decode(errors="ignore").strip()
                st = self._parse_line(line2)
            return st
        except Exception as e:
            self._log(format_current_exception(f"SerialOSSD error: {e}"))
            return None
