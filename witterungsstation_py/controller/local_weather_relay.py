from __future__ import annotations

from typing import Protocol

from model.dto import WeatherDTO

from controller.runtime_parsers import parse_dt


class DataHandlerWeatherDrainPort(Protocol):
    def drain_weather_events(self) -> list[WeatherDTO]: ...


class LocalWeatherRelay:
    def __init__(self, *, data_handler: DataHandlerWeatherDrainPort, view, post) -> None:
        self._data_handler = data_handler
        self._view = view
        self._post = post

    def apply(self) -> list[WeatherDTO]:
        drain = getattr(self._data_handler, "drain_weather_events", None)
        if not callable(drain):
            return []

        try:
            raw_events = drain()
        except Exception:
            return []

        events: list[WeatherDTO] = raw_events if isinstance(raw_events, list) else []
        if not events:
            return []

        for entry in events:
            payload = {
                "temp": float(getattr(entry, "temp", 0.0)),
                "pressure": float(getattr(entry, "pressure", 0.0)),
                "light": float(getattr(entry, "light", 0.0)),
                "winds": float(getattr(entry, "winds", 0.0)),
                "winddir": str(getattr(entry, "winddir", "")),
                "rain": float(getattr(entry, "rain", 0.0)),
                "humidity": float(getattr(entry, "humidity", 0.0)),
                "time": parse_dt(getattr(entry, "time", None)),
            }
            self._post(lambda p=payload: self._view.update_weather(p))

        return events
