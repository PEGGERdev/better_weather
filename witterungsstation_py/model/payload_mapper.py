from __future__ import annotations

from datetime import datetime

from model.dto import OSSDEntryDTO, WeatherDTO, WitterungsstationPyStateDTO
from model.ossd_status import normalize_ossd_status


def _iso(ts: datetime | None) -> str | None:
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts.isoformat()
    return str(ts)


def weather_to_payload(weather: WeatherDTO) -> dict | None:
    try:
        payload = {
            "temp": float(weather.temp) if weather.temp is not None else None,
            "pressure": float(weather.pressure) if weather.pressure is not None else None,
            "light": float(weather.light) if weather.light is not None else None,
            "winds": float(weather.winds) if weather.winds is not None else None,
            "winddir": str(weather.winddir or "").strip().upper(),
            "rain": float(weather.rain) if weather.rain is not None else None,
            "humidity": float(weather.humidity) if weather.humidity is not None else None,
            "time": _iso(getattr(weather, "time", None)),
        }
    except Exception:
        return None

    required = ("temp", "pressure", "light", "winds", "rain", "humidity")
    if any(payload[key] is None for key in required):
        return None

    if not (850.0 <= payload["pressure"] <= 1200.0):
        return None
    if not (0.0 <= payload["humidity"] <= 100.0):
        return None
    if payload["light"] < 0.0 or payload["winds"] < 0.0 or payload["rain"] < 0.0:
        return None
    if not payload["winddir"]:
        return None

    return payload


def ossd_to_payload(entry: OSSDEntryDTO) -> dict | None:
    try:
        status = normalize_ossd_status(entry.ossdStatus)
        if status is None:
            return None

        lichtgitter_nr = int(entry.lichtgitterNr)
        ossd_nr = int(entry.ossdNr)
        if lichtgitter_nr not in (1, 2) or ossd_nr not in (1, 2):
            return None

        return {
            "time": _iso(getattr(entry, "time", None)),
            "lichtgitterNr": lichtgitter_nr,
            "ossdNr": ossd_nr,
            "ossdStatus": status,
        }
    except Exception:
        return None


def witterungsstation_py_state_to_payload(entry: WitterungsstationPyStateDTO) -> dict | None:
    try:
        state = str(entry.state or "").strip().lower()
        if state not in {"start", "stop"}:
            return None

        return {
            "time": _iso(getattr(entry, "time", None)),
            "state": state,
        }
    except Exception:
        return None
