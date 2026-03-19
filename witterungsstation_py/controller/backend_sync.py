from __future__ import annotations

import builtins
import time
from typing import Optional, Protocol

from model.dto import WeatherDTO
from model.ports import TelemetryPort

from controller.runtime_parsers import parse_dt, parse_oid


class WeatherLiveReaderPort(Protocol):
    def read(self) -> Optional[dict]: ...


class BackendSync:
    def __init__(
        self,
        *,
        view,
        model_db: TelemetryPort,
        post,
        weather_live_reader: Optional[WeatherLiveReaderPort] = None,
        backend_interval_sec: float = 30.0,
        publish_live_weather: builtins.bool = True,
        sync_backend_ossd: builtins.bool = True,
    ) -> None:
        self._view = view
        self._db = model_db
        self._post = post
        self._weather_live_reader = weather_live_reader
        self._publish_live_weather = bool(publish_live_weather)
        self._sync_backend_ossd = bool(sync_backend_ossd)
        self._backend_interval = max(1.0, float(backend_interval_sec))
        self._next_backend_poll = 0.0
        self._weather_live_seen = False
        self._weather_live_last_warn = 0.0
        self._latest_live_weather: Optional[dict] = None
        self._latest_local_weather: Optional[WeatherDTO] = None
        self._last_posted_weather_key: Optional[str] = None
        self._seen_event_ids: set[str] = set()
        self._seen_event_order: list[str] = []
        self._seen_event_cap = 4000

    def reset_poll_schedule(self) -> None:
        self._next_backend_poll = 0.0

    def poll(self, *, has_local_ossd_events: builtins.bool, latest_local_weather: Optional[WeatherDTO] = None) -> bool:
        got_live_weather = False
        if latest_local_weather is not None:
            self._latest_local_weather = latest_local_weather
        if self._weather_live_reader is not None:
            got_live_weather = self._poll_live_weather()

        now_mono = time.monotonic()
        if now_mono < self._next_backend_poll:
            return got_live_weather

        self._next_backend_poll = now_mono + self._backend_interval
        self._post_latest_weather()
        if has_local_ossd_events or not self._sync_backend_ossd:
            return got_live_weather
        self._poll_backend_ossd()
        return got_live_weather

    def _poll_live_weather(self) -> bool:
        live_weather = self._weather_live_reader.read() if self._weather_live_reader else None
        if live_weather:
            self._latest_live_weather = live_weather
            if not self._weather_live_seen:
                self._weather_live_seen = True
                self._post(lambda: self._view.append_log("Weather-Live (direkt) aktiv."))
            live_payload = {
                "temp": live_weather.get("temp"),
                "pressure": live_weather.get("pressure"),
                "light": live_weather.get("light"),
                "winds": live_weather.get("winds"),
                "winddir": live_weather.get("winddir"),
                "rain": live_weather.get("rain"),
                "humidity": live_weather.get("humidity"),
                "time": parse_dt(live_weather.get("time")),
            }
            self._post(lambda p=live_payload: self._view.update_weather(p))
            return True

        now_mono = time.monotonic()
        if now_mono - self._weather_live_last_warn >= 10.0:
            self._weather_live_last_warn = now_mono
            self._post(lambda: self._view.append_log("Weather-Live: aktuell keine direkten HID-Daten."))
        return False

    def _post_latest_weather(self) -> None:
        if not self._publish_live_weather:
            return

        weather = self._latest_weather_dto()
        if weather is None:
            return

        weather_key = weather.time.isoformat()
        if self._last_posted_weather_key == weather_key:
            return

        self._db.post_weather(weather)
        self._last_posted_weather_key = weather_key

    def _latest_weather_dto(self) -> Optional[WeatherDTO]:
        if self._latest_local_weather is not None:
            return self._latest_local_weather
        if self._latest_live_weather is None:
            return None
        return WeatherDTO(
            temp=float(self._latest_live_weather.get("temp", 0.0)),
            pressure=float(self._latest_live_weather.get("pressure", 0.0)),
            light=float(self._latest_live_weather.get("light", 0.0)),
            winds=float(self._latest_live_weather.get("winds", 0.0)),
            winddir=str(self._latest_live_weather.get("winddir", "")),
            rain=float(self._latest_live_weather.get("rain", 0.0)),
            humidity=float(self._latest_live_weather.get("humidity", 0.0)),
            time=parse_dt(self._latest_live_weather.get("time")),
        )

    def _poll_backend_ossd(self) -> None:
        ossd_rows = self._db.get_ossd_recent(limit=300)
        if not ossd_rows:
            return

        state = [False, False, False, False]
        ordered = sorted(ossd_rows, key=lambda item: parse_dt(item.get("time")))
        for row in ordered:
            lg = int(row.get("lichtgitterNr", 1))
            on = int(row.get("ossdNr", 1))
            idx = (lg - 1) * 2 + (on - 1)
            state[idx] = str(row.get("ossdStatus", "E")).upper() == "O"

            oid = parse_oid(row.get("_id"))
            if oid and oid not in self._seen_event_ids:
                self._seen_event_ids.add(oid)
                self._seen_event_order.append(oid)
                if len(self._seen_event_order) > self._seen_event_cap:
                    old = self._seen_event_order.pop(0)
                    self._seen_event_ids.discard(old)
                ts = parse_dt(row.get("time"))
                label = f"LG{lg} OSSD{on}"
                self._post(lambda i=idx, t=ts, l=label: self._view.chart_add_ossd(i, t, l))

        self._post(lambda s=tuple(state): self._view.update_ossd(s))
        self._post(self._view.chart_redraw)
