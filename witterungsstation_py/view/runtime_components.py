from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class WeatherFieldBinding:
    id: str
    title: str
    payload_key: str
    unit: str = ""


_WEATHER_FIELDS: dict[str, WeatherFieldBinding] = {}


def register_weather_field(*, id: str, title: str, payload_key: str, unit: str = "") -> Callable[[type], type]:
    def decorator(cls: type) -> type:
        _WEATHER_FIELDS[id] = WeatherFieldBinding(
            id=id,
            title=title,
            payload_key=payload_key,
            unit=unit,
        )
        return cls

    return decorator


def get_weather_fields() -> list[WeatherFieldBinding]:
    return [_WEATHER_FIELDS[k] for k in sorted(_WEATHER_FIELDS)]


@register_weather_field(id="temp", title="Temp:", payload_key="temp", unit=" °C")
class _TempField:
    pass


@register_weather_field(id="pressure", title="Luftdruck:", payload_key="pressure", unit=" hPa")
class _PressureField:
    pass


@register_weather_field(id="light", title="Lichteinstrahlung:", payload_key="light")
class _LightField:
    pass


@register_weather_field(id="winds", title="Windgeschw.:", payload_key="winds", unit=" km/h")
class _WindSpeedField:
    pass


@register_weather_field(id="winddir", title="Windrichtung:", payload_key="winddir")
class _WindDirectionField:
    pass


@register_weather_field(id="rain", title="Regen:", payload_key="rain", unit=" mm")
class _RainField:
    pass


@register_weather_field(id="humidity", title="Luftfeuchte:", payload_key="humidity", unit=" %")
class _HumidityField:
    pass
