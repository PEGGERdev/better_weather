from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field
from datetime import datetime
import math
from typing import Any, cast


CHANNEL_LABELS = ["LG1 OSSD1", "LG1 OSSD2", "LG2 OSSD1", "LG2 OSSD2"]


@dataclass
class ChartDataBuffer:
    keep: int = 3000
    weather_x: list[datetime] = field(default_factory=list)
    temp: list[float] = field(default_factory=list)
    pressure: list[float] = field(default_factory=list)
    humidity: list[float] = field(default_factory=list)
    light: list[float] = field(default_factory=list)
    winds: list[float] = field(default_factory=list)
    rain: list[float] = field(default_factory=list)
    winddir: list[str] = field(default_factory=list)
    ossd_x: list[datetime] = field(default_factory=list)
    ossd_channel: list[int] = field(default_factory=list)
    ossd_label: list[str] = field(default_factory=list)

    def append_weather(self, payload: dict) -> None:
        timestamp = payload.get("time")
        temp = payload.get("temp")
        if timestamp is None or temp is None:
            return

        self.weather_x.append(timestamp)
        self.temp.append(float(temp))
        self.pressure.append(self._as_float(payload.get("pressure")))
        self.humidity.append(self._as_float(payload.get("humidity")))
        self.light.append(self._as_float(payload.get("light")))
        self.winds.append(self._as_float(payload.get("winds")))
        self.rain.append(self._as_float(payload.get("rain")))
        self.winddir.append(str(payload.get("winddir") or ""))
        self._trim_weather()

    def append_ossd(self, channel_idx: int, ts: datetime, label: str) -> None:
        if channel_idx not in range(len(CHANNEL_LABELS)):
            return
        self.ossd_x.append(ts)
        self.ossd_channel.append(channel_idx)
        self.ossd_label.append(label)
        self._trim_ossd()

    def nearest_weather_idx(self, ts: datetime) -> int | None:
        if not self.weather_x:
            return None
        pos = bisect_left(self.weather_x, ts)
        if pos <= 0:
            return 0
        if pos >= len(self.weather_x):
            return len(self.weather_x) - 1
        before = self.weather_x[pos - 1]
        after = self.weather_x[pos]
        if abs((ts - before).total_seconds()) <= abs((after - ts).total_seconds()):
            return pos - 1
        return pos

    def weather_summary_for(self, ts: datetime) -> str:
        idx = self.nearest_weather_idx(ts)
        if idx is None:
            return "keine Wetterdaten"
        return (
            f"T={self.temp[idx]:.1f}C, P={self.pressure[idx]:.1f}hPa\n"
            f"H={self.humidity[idx]:.1f}%, L={self.light[idx]:.0f}\n"
            f"W={self.winds[idx]:.1f}km/h, R={self.rain[idx]:.1f}mm, D={self.winddir[idx] or '?'}"
        )

    @staticmethod
    def _as_float(value: object) -> float:
        if value is None:
            return math.nan
        return float(cast(Any, value))

    def _trim_weather(self) -> None:
        if len(self.weather_x) <= self.keep:
            return
        self.weather_x = self.weather_x[-self.keep :]
        self.temp = self.temp[-self.keep :]
        self.pressure = self.pressure[-self.keep :]
        self.humidity = self.humidity[-self.keep :]
        self.light = self.light[-self.keep :]
        self.winds = self.winds[-self.keep :]
        self.rain = self.rain[-self.keep :]
        self.winddir = self.winddir[-self.keep :]

    def _trim_ossd(self) -> None:
        if len(self.ossd_x) <= self.keep:
            return
        self.ossd_x = self.ossd_x[-self.keep :]
        self.ossd_channel = self.ossd_channel[-self.keep :]
        self.ossd_label = self.ossd_label[-self.keep :]
