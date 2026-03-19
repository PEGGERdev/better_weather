from __future__ import annotations

from typing import Tuple

from shared.config import env_bool, env_float, env_int
from shared.parser_registry import BaseParser, register_parser


@register_parser(
    name="weather",
    data_type="hid",
    description="Parses weather data from HID weather station",
)
class WeatherParser(BaseParser):
    """Parses weather data from raw HID bytes."""
    
    WINDDIR_MAP = {
        0: "N", 1: "NNE", 2: "NE", 3: "NEE", 4: "E", 5: "SEE", 6: "SE", 7: "SSE",
        8: "S", 9: "SSW", 10: "SW", 11: "SWW", 12: "W", 13: "NWW", 14: "NW", 15: "NNW",
    }
    
    def __init__(self, log=None) -> None:
        self._log = log or (lambda _: None)
        self._load_calibration()
    
    def _load_calibration(self) -> None:
        self._debug = env_bool("WEATHER_DEBUG", False)
        self._ptr_swap = env_bool("WEATHER_PTR_SWAP", False)
        self._temp_scale = env_float("WEATHER_TEMP_SCALE", 0.1)
        self._pressure_scale = env_float("WEATHER_PRESSURE_SCALE", 0.1)
        self._wind_scale = env_float("WEATHER_WIND_SCALE", 0.1)
        self._wind_offset = env_float("WEATHER_WIND_OFFSET", 1.2)
        self._rain_factor = env_float("WEATHER_RAIN_FACTOR", 0.3)
        self._light_div = env_int("WEATHER_LIGHT_DIV", 10)
    
    @classmethod
    def parse(cls, raw: bytes):
        if not cls.validate(raw):
            return None
        
        try:
            humidity = float(raw[4])
            temp_raw = (raw[6] << 8) | raw[5]
            press_raw = (raw[8] << 8) | raw[7]
            temp = float(temp_raw) * 0.1
            pressure = float(press_raw) * 0.1
            wind_raw = ((raw[10] & 0x0F) << 8) | raw[9]
            winds = max(0.0, float(wind_raw) * 0.1 - 1.2)
            winddir = cls.WINDDIR_MAP.get(raw[12], "")
            rain = float(raw[13]) * 0.3
            light_raw = (raw[18] << 16) | (raw[17] << 8) | raw[16]
            light = float(light_raw // 10)
            
            return {
                "temp": temp,
                "pressure": pressure,
                "humidity": humidity,
                "winds": winds,
                "winddir": winddir,
                "rain": rain,
                "light": light,
            }
        except Exception:
            return None
    
    @classmethod
    def validate(cls, data) -> bool:
        if not isinstance(data, (bytes, bytearray)):
            return False
        return len(data) >= 19
    
    def parse_with_calibration(self, raw: bytes):
        if not self.validate(raw):
            return None
        
        try:
            humidity = float(raw[4])
            temp_raw = (raw[6] << 8) | raw[5]
            press_raw = (raw[8] << 8) | raw[7]
            temp = float(temp_raw) * self._temp_scale
            pressure = float(press_raw) * self._pressure_scale
            wind_raw = ((raw[10] & 0x0F) << 8) | raw[9]
            winds = max(0.0, float(wind_raw) * self._wind_scale - self._wind_offset)
            winddir = self.WINDDIR_MAP.get(raw[12], "")
            rain = float(raw[13]) * self._rain_factor
            light_raw = (raw[18] << 16) | (raw[17] << 8) | raw[16]
            light = float(light_raw // max(1, self._light_div))
            
            if self._debug:
                self._log(
                    f"WEATHER_DEBUG: raw[0:19]={raw[:19].hex(' ')} "
                    f"temp={temp} pressure={pressure} humidity={humidity} "
                    f"winds={winds} dir={winddir} rain={rain} light={light}"
                )
            
            return {
                "temp": temp,
                "pressure": pressure,
                "humidity": humidity,
                "winds": winds,
                "winddir": winddir,
                "rain": rain,
                "light": light,
            }
        except Exception as exc:
            self._log(f"Weather parse error: {exc}")
            return None
    
    @staticmethod
    def get_pointer_bytes(raw: bytes, swap: bool = False) -> Tuple[int, int]:
        b0 = raw[0] if len(raw) > 0 else 0
        b1 = raw[1] if len(raw) > 1 else 0
        if swap:
            return b1, b0
        return b0, b1

    @classmethod
    def is_sane_payload(cls, data: dict) -> bool:
        return len(cls.sanity_issues(data)) == 0

    @classmethod
    def sanity_issues(cls, data: dict) -> list[str]:
        try:
            required = {"temp", "pressure", "humidity", "winds", "winddir", "rain", "light"}
            missing = sorted(required.difference(set(data.keys())))
            if missing:
                return [f"missing={','.join(missing)}"]

            temp = float(data.get("temp", 0.0))
            pressure = float(data.get("pressure", 0.0))
            humidity = float(data.get("humidity", 0.0))
            winds = float(data.get("winds", 0.0))
            rain = float(data.get("rain", 0.0))
            light = float(data.get("light", 0.0))
            winddir = str(data.get("winddir", "")).strip().upper()

            issues: list[str] = []
            if not (-50.0 <= temp <= 60.0):
                issues.append(f"temp={temp}")
            if not (850.0 <= pressure <= 1200.0):
                issues.append(f"pressure={pressure}")
            if not (0.0 <= humidity <= 100.0):
                issues.append(f"humidity={humidity}")
            if not (0.0 <= winds <= 120.0):
                issues.append(f"winds={winds}")
            if not (0.0 <= rain <= 5000.0):
                issues.append(f"rain={rain}")
            if not (0.0 <= light <= 2_000_000.0):
                issues.append(f"light={light}")
            if winddir not in cls.WINDDIR_MAP.values():
                issues.append(f"winddir={winddir or '<empty>'}")
            return issues
        except Exception:
            return ["payload_parse_error"]
