from __future__ import annotations
from typing import Optional
from dataclasses import dataclass
import os, sys, pathlib, ctypes, time
import hid

from model.ports import WeatherSensorPort, ClockPort

_WINDDIR = {0:"N",1:"NNE",2:"NE",3:"NEE",4:"E",5:"SEE",6:"SE",7:"SSE",
            8:"S",9:"SSW",10:"SW",11:"SWW",12:"W",13:"NWW",14:"NW",15:"NNW"}

@dataclass
class _Weather:
    temp: float; preassure: float; light: float; winds: float
    winddir: str; rain: float; humidity: float; time: object

class HidWeatherSensor(WeatherSensorPort):
    """Spricht HID-Wetterstation an (Windows, hidapi)."""
    def __init__(self, vid: int, pid: int, clock: ClockPort, report_size: int = 32):
        self.vid, self.pid, self.clock, self.report_size = vid, pid, clock, report_size
        self._dev: Optional[hid.device] = None

    def _ensure_open(self) -> bool:
        if self._dev: return True
        try:
            d = hid.device(); d.open(self.vid, self.pid); d.set_nonblocking(True)
            self._dev = d; return True
        except Exception:
            self._dev = None; return False

    def _write_hex(self, hex_bytes: str, out_len: int) -> bool:
        if not self._ensure_open(): return False
        parts = [p for p in hex_bytes.split() if p]
        payload = bytes(int(p,16)&0xFF for p in parts)
        if len(payload) < out_len: payload += b"\x00"*(out_len-len(payload))
        data = bytes([0]) + payload
        try: return self._dev.write(data) > 0
        except Exception: return False

    def _read_bytes(self, want: int, timeout: float) -> bytes:
        if not self._ensure_open(): return b""
        out = bytearray(); end = time.time() + timeout
        while len(out) < want and time.time() < end:
            try:
                raw = self._dev.read(65)
                if raw: out.extend(raw[1:])
                else: time.sleep(0.02)
            except Exception: time.sleep(0.02)
        return bytes(out[:want])

    def read_weather(self) -> Optional[_Weather]:
        if not self._write_hex("A1 00 1E 20 A1 00 1E 20", 8): return None
        ptr = self._read_bytes(self.report_size, 0.6)
        b0 = ptr[0] if len(ptr)>0 else 0; b1 = ptr[1] if len(ptr)>1 else 0
        cmd = bytes([0xA1,b1,b0,0x20,0xA1,b1,b0,0x20])
        if not self._write_hex(" ".join(f"{x:02X}" for x in cmd), 8): return None
        raw = self._read_bytes(self.report_size, 1.2)
        if len(raw) < 19: return None
        try:
            humidity  = float(raw[4])
            temp      = float(raw[6]*256 + raw[5]) * 0.1
            preassure = float(raw[8]*256 + raw[7]) * 0.1
            winds     = float((raw[10]&15) + raw[9]) * 0.1
            winddir   = _WINDDIR.get(raw[12], "")
            rain      = float(raw[13]) * 0.3
            light     = int((raw[18]*65536 + raw[17]*256 + raw[16]) // 10)
        except Exception:
            return None
        return _Weather(temp, preassure, light, winds, winddir, rain, humidity, self.clock.now())
