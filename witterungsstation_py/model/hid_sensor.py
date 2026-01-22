from __future__ import annotations

"""
Witterungstester – HidWeatherSensor (HID Adapter)

Problem context
- Values shown in "From Hardware" do not match the physical weather station display.
- This points to decoding/parsing issues (byte order, bit packing, scaling factors, or pointer command).

Design goals
- KISS: keep decoding readable.
- DRY : centralize byte helpers + scaling config.
- Debuggable: optional raw-byte logging to verify mapping against the station display.

Configuration (ENV)
- WEATHER_DEBUG=1              -> log pointer + raw bytes + decoded values
- WEATHER_PTR_SWAP=1           -> swap pointer bytes in the follow-up command (device-specific)
- WEATHER_TEMP_SCALE=0.1       -> default 0.1
- WEATHER_PRESSURE_SCALE=0.1   -> default 0.1
- WEATHER_WIND_SCALE=0.1       -> default 0.1
- WEATHER_RAIN_FACTOR=0.3      -> default 0.3
- WEATHER_LIGHT_DIV=10         -> default 10
"""

from typing import Optional, Callable, Dict
from dataclasses import dataclass
import os
import time
import hid

from model.ports import WeatherSensorPort, ClockPort
from exception_handler import format_current_exception


_WINDDIR = {
    0: "N", 1: "NNE", 2: "NE", 3: "NEE", 4: "E", 5: "SEE", 6: "SE", 7: "SSE",
    8: "S", 9: "SSW", 10: "SW", 11: "SWW", 12: "W", 13: "NWW", 14: "NW", 15: "NNW",
}


@dataclass
class _Weather:
    temp: float
    preassure: float
    light: float
    winds: float
    winddir: str
    rain: float
    humidity: float
    time: object


def _env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    try:
        return float(v) if v is not None else default
    except Exception:
        return default


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    try:
        return int(v) if v is not None else default
    except Exception:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def _u16le(lo: int, hi: int) -> int:
    """Unsigned 16-bit little-endian."""
    return (hi << 8) | lo


def _u24le(b0: int, b1: int, b2: int) -> int:
    """Unsigned 24-bit little-endian."""
    return (b2 << 16) | (b1 << 8) | b0


class HidWeatherSensor(WeatherSensorPort):
    """Speaks to HID weather station (Windows, hidapi)."""

    def __init__(
        self,
        vid: int,
        pid: int,
        clock: ClockPort,
        report_size: int = 32,
        log: Callable[[str], None] | None = None,
    ):
        self.vid, self.pid, self.clock, self.report_size = vid, pid, clock, report_size
        self._dev: Optional[hid.device] = None
        self._log = log or (lambda *_: None)

        # Rate-limited logging to avoid console spam.
        self._err_gate: Dict[str, float] = {}

        # Decoding knobs (device-specific; keep defaults matching your previous code).
        self._debug = _env_bool("WEATHER_DEBUG", False)
        self._ptr_swap = _env_bool("WEATHER_PTR_SWAP", False)

        self._temp_scale = _env_float("WEATHER_TEMP_SCALE", 0.1)
        self._pressure_scale = _env_float("WEATHER_PRESSURE_SCALE", 0.1)
        self._wind_scale = _env_float("WEATHER_WIND_SCALE", 0.1)

        self._rain_factor = _env_float("WEATHER_RAIN_FACTOR", 0.3)
        self._light_div = _env_int("WEATHER_LIGHT_DIV", 10)

    # ---------------- internal logging ----------------
    def _log_rl(self, key: str, context: str, cooldown_sec: float = 15.0) -> None:
        now = time.time()
        last = self._err_gate.get(key, 0.0)
        if now - last < cooldown_sec:
            return
        self._err_gate[key] = now
        self._log(format_current_exception(context))

    def _dbg(self, text: str) -> None:
        if self._debug:
            self._log(text)

    # ---------------- hid helpers ----------------
    def _ensure_open(self) -> bool:
        if self._dev:
            return True
        try:
            d = hid.device()
            d.open(self.vid, self.pid)
            d.set_nonblocking(True)
            self._dev = d
            return True
        except Exception:
            self._dev = None
            self._log_rl("open", f"HID open failed (VID=0x{self.vid:04X}, PID=0x{self.pid:04X})")
            return False

    def _write_hex(self, hex_bytes: str, out_len: int) -> bool:
        if not self._ensure_open():
            return False
        parts = [p for p in hex_bytes.split() if p]
        payload = bytes(int(p, 16) & 0xFF for p in parts)
        if len(payload) < out_len:
            payload += b"\x00" * (out_len - len(payload))
        data = bytes([0]) + payload  # report-id prefix
        try:
            return self._dev.write(data) > 0
        except Exception:
            self._log_rl("write", "HID write failed")
            return False

    def _read_bytes(self, want: int, timeout: float) -> bytes:
        if not self._ensure_open():
            return b""
        out = bytearray()
        end = time.time() + timeout
        while len(out) < want and time.time() < end:
            try:
                raw = self._dev.read(65)
                if raw:
                    out.extend(raw[1:])  # drop report-id
                else:
                    time.sleep(0.02)
            except Exception:
                self._log_rl("read", "HID read failed")
                time.sleep(0.02)
        return bytes(out[:want])

    # ---------------- WeatherSensorPort ----------------
    def read_weather(self) -> Optional[_Weather]:
        """
        Reads weather values from the HID device.

        NOTE
        - This device uses a pointer-like request: first fetch pointer bytes, then request payload.
        - If values mismatch, enable WEATHER_DEBUG=1 and compare raw bytes with the station display.
        - If pointer order is wrong, try WEATHER_PTR_SWAP=1.
        """
        if not self._write_hex("A1 00 1E 20 A1 00 1E 20", 8):
            return None

        ptr = self._read_bytes(self.report_size, 0.6)
        b0 = ptr[0] if len(ptr) > 0 else 0
        b1 = ptr[1] if len(ptr) > 1 else 0

        # Device-specific: some devices expect (b0,b1), some (b1,b0).
        p_lo, p_hi = (b1, b0) if self._ptr_swap else (b0, b1)

        cmd = bytes([0xA1, p_hi, p_lo, 0x20, 0xA1, p_hi, p_lo, 0x20])
        if not self._write_hex(" ".join(f"{x:02X}" for x in cmd), 8):
            return None

        raw = self._read_bytes(self.report_size, 1.2)
        if len(raw) < 19:
            return None

        try:
            # --- decode ---
            humidity = float(raw[4])

            # temp/pressure: most devices store as little-endian 16-bit with scale 0.1
            temp_raw = _u16le(raw[5], raw[6])
            press_raw = _u16le(raw[7], raw[8])

            temp = float(temp_raw) * self._temp_scale
            preassure = float(press_raw) * self._pressure_scale

            # wind: your previous formula looked wrong.
            # Common pattern: low byte in raw[9], high nibble in raw[10] (12-bit).
            wind_raw = ((raw[10] & 0x0F) << 8) | raw[9]
            winds = float(wind_raw) * self._wind_scale

            winddir = _WINDDIR.get(raw[12], "")

            # rain: keep your factor but allow calibration via ENV
            rain = float(raw[13]) * self._rain_factor

            # light: 24-bit value, then divide (device-specific); keep configurable divisor
            light_raw = _u24le(raw[16], raw[17], raw[18])
            light = float(light_raw // max(1, self._light_div))

            # --- debug output ---
            self._dbg(
                "WEATHER_DEBUG: "
                f"ptr=({b0:02X},{b1:02X}) ptr_used=({p_lo:02X},{p_hi:02X}) "
                f"raw[0:19]={raw[:19].hex(' ')} "
                f"temp_raw={temp_raw} temp={temp} "
                f"press_raw={press_raw} press={preassure} "
                f"wind_raw={wind_raw} wind={winds} "
                f"dir={winddir} rain={rain} light_raw={light_raw} light={light} hum={humidity}"
            )

        except Exception:
            self._log_rl("parse", "HID weather parse failed", cooldown_sec=30.0)
            return None

        return _Weather(temp, preassure, light, winds, winddir, rain, humidity, self.clock.now())
