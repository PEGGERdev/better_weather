from __future__ import annotations
import time, re
from typing import Optional, Tuple, Callable
import serial

from model.ports import OSSDPort, ClockPort
from exception_handler import format_current_exception


class SerialOSSD(OSSDPort):
    """
    Liest den Arduino über Serial.
    Erwartete Antwort auf 'G\\n': 'G0O,G1O,G2O,G3O' (oder ...E).
    """
    def __init__(self, port: str, baud: int, clock: ClockPort, log: Callable[[str], None] | None = None):
        self._ser = serial.Serial(port=port, baudrate=baud, timeout=1.0)
        self._clock = clock
        self._log = log or (lambda *_: None)
        time.sleep(0.2)

    def _parse_line(self, line: str) -> Optional[Tuple[bool, bool, bool, bool]]:
        m = re.findall(r"G([0-3])([OE])", line)
        if len(m) != 4:
            return None
        vals = [None, None, None, None]
        for idx, ch in m:
            vals[int(idx)] = (ch == "O")  # O=OK true
        if any(v is None for v in vals):
            return None
        return tuple(bool(v) for v in vals)  # type: ignore

    def read_state(self) -> Optional[Tuple[bool, bool, bool, bool]]:
        try:
            self._ser.reset_input_buffer()
            self._ser.write(b"G\n")
            self._ser.flush()
            line = self._ser.readline().decode(errors="ignore").strip()
            st = self._parse_line(line)
            if st is None:
                # evtl. Interrupt-String ohne 'G..' – wir versuchen noch ein zweites read
                time.sleep(0.05)
                line2 = self._ser.readline().decode(errors="ignore").strip()
                st = self._parse_line(line2)
            return st
        except Exception as e:
            self._log(format_current_exception(f"SerialOSSD Fehler: {e}"))
            return None
