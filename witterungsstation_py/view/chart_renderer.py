from __future__ import annotations

from typing import Any, cast

from matplotlib import dates as mdates
from matplotlib.figure import Figure

from view.chart_model import CHANNEL_LABELS, ChartDataBuffer


class WeatherChartRenderer:
    def __init__(self, figure: Figure) -> None:
        self._fig = figure
        self._event_ax = None
        self._event_scatter = None
        self._hover_ann = None
        self.setup_axes()

    def setup_axes(self) -> None:
        self._fig.clear()
        axes = cast(Any, self._fig.subplots(4, 1, sharex=True, height_ratios=[2.2, 1.4, 1.4, 1.0]))
        self._ax_temp, self._ax_humidity, self._ax_light, self._event_ax = axes
        self._ax_pressure = self._ax_temp.twinx()
        self._ax_wind = self._ax_humidity.twinx()
        self._ax_rain = self._ax_light.twinx()

        self._ax_temp.set_title("Wetterverlauf und OSSD-Ereignisse")
        self._ax_temp.set_ylabel("Temp [C]", color="#e63946")
        self._ax_pressure.set_ylabel("Druck [hPa]", color="#1d3557")
        self._ax_humidity.set_ylabel("Feuchte [%]", color="#2a9d8f")
        self._ax_wind.set_ylabel("Wind [km/h]", color="#457b9d")
        self._ax_light.set_ylabel("Licht", color="#f4a261")
        self._ax_rain.set_ylabel("Regen [mm]", color="#6a4c93")
        self._event_ax.set_ylabel("OSSD")
        self._event_ax.set_xlabel("Zeit")
        self._event_ax.set_yticks(range(len(CHANNEL_LABELS)))
        self._event_ax.set_yticklabels(CHANNEL_LABELS)

        for axis in (self._ax_temp, self._ax_humidity, self._ax_light, self._event_ax):
            axis.grid(True, alpha=0.2)

        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        self._event_ax.xaxis.set_major_locator(locator)
        self._event_ax.xaxis.set_major_formatter(formatter)

        self._hover_ann = self._event_ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="#f8fafc", ec="#475569", alpha=0.95),
            arrowprops=dict(arrowstyle="->", color="#475569"),
        )
        self._hover_ann.set_visible(False)
        self._event_scatter = self._event_ax.scatter([], [], marker="x", s=80, linewidths=1.8, color="#d62828")

    def redraw(self, data: ChartDataBuffer) -> None:
        self.setup_axes()

        if data.weather_x:
            weather_x = cast(Any, data.weather_x)
            self._ax_temp.plot(weather_x, data.temp, linewidth=1.8, color="#e63946", label="Temp")
            self._ax_temp.fill_between(weather_x, data.temp, alpha=0.12, color="#e63946")
            self._ax_pressure.plot(weather_x, data.pressure, linewidth=1.3, color="#1d3557", label="Druck")

            self._ax_humidity.plot(weather_x, data.humidity, linewidth=1.4, color="#2a9d8f", label="Feuchte")
            self._ax_wind.plot(weather_x, data.winds, linewidth=1.2, linestyle="--", color="#457b9d", label="Wind")

            self._ax_light.plot(weather_x, data.light, linewidth=1.3, color="#f4a261", label="Licht")
            self._ax_light.fill_between(weather_x, data.light, alpha=0.10, color="#f4a261")
            self._ax_rain.step(weather_x, data.rain, where="mid", linewidth=1.2, color="#6a4c93", label="Regen")

            self._ax_temp.legend(loc="upper left")
            self._ax_pressure.legend(loc="upper right")
            self._ax_humidity.legend(loc="upper left")
            self._ax_wind.legend(loc="upper right")
            self._ax_light.legend(loc="upper left")
            self._ax_rain.legend(loc="upper right")

        if data.ossd_x:
            event_ax = cast(Any, self._event_ax)
            self._event_scatter = event_ax.scatter(
                cast(Any, data.ossd_x),
                data.ossd_channel,
                marker="x",
                s=80,
                linewidths=1.8,
                color="#d62828",
                zorder=3,
            )
            for ts in data.ossd_x:
                event_ax.axvline(ts, color="#d62828", alpha=0.10, linewidth=0.8)

        self._fig.canvas.draw_idle()

    def handle_hover(self, event, data: ChartDataBuffer) -> None:
        if not self._hover_ann or not self._event_scatter or event.inaxes != self._event_ax:
            if self._hover_ann and self._hover_ann.get_visible():
                self._hover_ann.set_visible(False)
                self._fig.canvas.draw_idle()
            return

        contains, info = self._event_scatter.contains(event)
        indices = info.get("ind") if isinstance(info, dict) else None
        if not contains or indices is None or len(indices) == 0:
            if self._hover_ann.get_visible():
                self._hover_ann.set_visible(False)
                self._fig.canvas.draw_idle()
            return

        idx = int(indices[0])
        ts = data.ossd_x[idx]
        channel = data.ossd_channel[idx]
        self._hover_ann.xy = (ts, channel)
        self._hover_ann.set_text(f"{data.ossd_label[idx]}\n{data.weather_summary_for(ts)}")
        self._hover_ann.set_visible(True)
        self._fig.canvas.draw_idle()
