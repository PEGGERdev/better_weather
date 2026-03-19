from __future__ import annotations

from typing import Callable, Optional, Tuple

from data_handler.registry import register_service
from shared.parsers import OssdParser
from shared.serial_client import SerialClient


@register_service(kind="reader", name="ossd")
class OssdReader:
    def __init__(self, serial_client: SerialClient, parser: OssdParser, log: Callable[[str], None], debug: bool = False) -> None:
        self._serial = serial_client
        self._parser = parser
        self._log = log
        self._debug = debug

    def read(self) -> Optional[Tuple[bool, bool, bool, bool]]:
        line = self._serial.query_line("G", retries=1)
        if line is None:
            return None
        result = self._parser.parse(line)
        if self._debug:
            self._log(f"OSSD line: {repr(line)} -> {result}")
        return result
