from __future__ import annotations

from typing import Protocol

from model.dto import OSSDEntryDTO
from controller.runtime_parsers import parse_dt


class DataHandlerDrainPort(Protocol):
    def drain_ossd_events(self) -> list[OSSDEntryDTO]: ...


class LocalOssdRelay:
    def __init__(self, *, data_handler: DataHandlerDrainPort, view, post) -> None:
        self._data_handler = data_handler
        self._view = view
        self._post = post
        self._local_ossd_state: list[bool] = [False, False, False, False]

    def apply(self) -> list[OSSDEntryDTO]:
        drain = getattr(self._data_handler, "drain_ossd_events", None)
        if not callable(drain):
            return []

        try:
            raw_events = drain()
        except Exception:
            return []

        events: list[OSSDEntryDTO] = raw_events if isinstance(raw_events, list) else []
        if not events:
            return []

        for entry in events:
            lg = int(getattr(entry, "lichtgitterNr", 1))
            on = int(getattr(entry, "ossdNr", 1))
            status = str(getattr(entry, "ossdStatus", "E")).upper()
            idx = (lg - 1) * 2 + (on - 1)
            if idx not in (0, 1, 2, 3):
                continue
            self._local_ossd_state[idx] = status == "O"

            ts = parse_dt(getattr(entry, "time", None))
            label = f"LG{lg} OSSD{on}"
            self._post(lambda i=idx, t=ts, l=label: self._view.chart_add_ossd(i, t, l))

        self._post(lambda s=tuple(self._local_ossd_state): self._view.update_ossd(s))
        self._post(self._view.chart_redraw)
        return events
