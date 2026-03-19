from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Any, Callable

from data_handler.contracts import BaseOutputHandler
from data_handler.registry import register_service


@register_service(kind="output", name="ipc")
class IpcOutputHandler(BaseOutputHandler):
    def __init__(self, log: Callable[[str], None]) -> None:
        self._log = log
        self._lock = None
        try:
            import threading

            self._lock = threading.Lock()
        except Exception:
            pass

    def _write(self, obj: dict[str, Any]) -> None:
        line = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        if self._lock:
            with self._lock:
                sys.stdout.write(line + "\n")
                sys.stdout.flush()
        else:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

    def emit_ossd(
        self,
        ts: datetime,
        lichtgitter_nr: int,
        ossd_nr: int,
        status: str,
    ) -> None:
        self._write(
            {
                "type": "ossd",
                "ts": ts.isoformat() if ts else None,
                "lichtgitterNr": lichtgitter_nr,
                "ossdNr": ossd_nr,
                "status": status,
            }
        )

    def emit_weather(
        self,
        ts: datetime,
        temp: float,
        pressure: float,
        humidity: float,
        winds: float,
        winddir: str,
        rain: float,
        light: float,
    ) -> None:
        self._write(
            {
                "type": "weather",
                "ts": ts.isoformat() if ts else None,
                "temp": temp,
                "pressure": pressure,
                "humidity": humidity,
                "winds": winds,
                "winddir": winddir,
                "rain": rain,
                "light": light,
            }
        )
