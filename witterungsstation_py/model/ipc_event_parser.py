from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Optional

from model.dto import OSSDEntryDTO, WeatherDTO
from model.ossd_status import normalize_ossd_status


@dataclass(frozen=True)
class ParsedIpcLine:
    kind: str
    payload: object


class IpcEventParser:
    def parse_line(self, line: str) -> Optional[ParsedIpcLine]:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            return None

        typ = obj.get("type")
        if typ == "ossd":
            return ParsedIpcLine(kind="ossd", payload=self._parse_ossd(obj))
        if typ == "weather":
            return ParsedIpcLine(kind="weather", payload=self._parse_weather(obj))
        return ParsedIpcLine(kind="unknown", payload=obj)

    @staticmethod
    def _parse_timestamp(value: object) -> datetime:
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except Exception:
                pass
        return datetime.now(UTC)

    def _parse_ossd(self, obj: dict[str, Any]) -> OSSDEntryDTO:
        return OSSDEntryDTO(
            time=self._parse_timestamp(obj.get("ts")),
            lichtgitterNr=int(obj.get("lichtgitterNr", 1)),
            ossdNr=int(obj.get("ossdNr", 1)),
            ossdStatus=normalize_ossd_status(obj.get("status")) or "E",
        )

    def _parse_weather(self, obj: dict[str, Any]) -> WeatherDTO:
        return WeatherDTO(
            temp=float(obj.get("temp", 0.0)),
            pressure=float(obj.get("pressure", 0.0)),
            light=float(obj.get("light", 0.0)),
            winds=float(obj.get("winds", 0.0)),
            winddir=str(obj.get("winddir", "")),
            rain=float(obj.get("rain", 0.0)),
            humidity=float(obj.get("humidity", 0.0)),
            time=self._parse_timestamp(obj.get("ts")),
        )
