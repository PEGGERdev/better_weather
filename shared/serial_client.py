from __future__ import annotations

"""
Generic Serial Client.

Reusable serial communication client used by data_handler and app.
"""

import time
from dataclasses import dataclass
from typing import Callable, Optional

import serial


@dataclass(frozen=True)
class SerialConfig:
    port: str
    baud: int
    timeout: float = 1.0


class SerialClient:
    def __init__(
        self,
        config: SerialConfig,
        log: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._config = config
        self._log = log or (lambda _: None)
        self._serial: Optional[serial.Serial] = None

    def open(self) -> bool:
        try:
            self._serial = serial.Serial(
                port=self._config.port,
                baudrate=self._config.baud,
                timeout=self._config.timeout,
            )
            time.sleep(0.1)
            self._log(f"Serial opened: {self._config.port} @ {self._config.baud}")
            return True
        except Exception as exc:
            self._log(f"Serial open failed: {exc}")
            return False

    def close(self) -> None:
        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None

    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def write(self, data: bytes) -> bool:
        if not self._serial:
            return False
        try:
            self._serial.write(data)
            self._serial.flush()
            return True
        except Exception as exc:
            self._log(f"Serial write error: {exc}")
            return False

    def write_line(self, line: str) -> bool:
        return self.write((line + "\n").encode("utf-8"))

    def read_line(self, timeout: Optional[float] = None) -> Optional[str]:
        if not self._serial:
            return None
        try:
            if timeout is not None:
                old_timeout = self._serial.timeout
                self._serial.timeout = timeout
            line = self._serial.readline().decode(errors="ignore").strip()
            if timeout is not None:
                self._serial.timeout = old_timeout
            return line if line else None
        except Exception as exc:
            self._log(f"Serial read error: {exc}")
            return None

    def reset_input_buffer(self) -> None:
        if self._serial:
            try:
                self._serial.reset_input_buffer()
            except Exception:
                pass

    def query_line(self, command: str, retries: int = 1) -> Optional[str]:
        if not self._serial:
            return None
        try:
            self.reset_input_buffer()
            self.write_line(command)
            line = self.read_line()
            if line:
                return line
            for _ in range(retries):
                time.sleep(0.05)
                line = self.read_line()
                if line:
                    return line
            return None
        except Exception as exc:
            self._log(f"Serial query error: {exc}")
            return None

    def __enter__(self) -> "SerialClient":
        self.open()
        return self

    def __exit__(self, *args) -> None:
        self.close()
