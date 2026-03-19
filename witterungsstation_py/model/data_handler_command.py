from __future__ import annotations

import os
import sys
from pathlib import Path


class DataHandlerCommand:
    def __init__(
        self,
        *,
        serial_port: str | None = None,
        serial_baud: int | None = None,
        hid_vid: int | None = None,
        hid_pid: int | None = None,
        poll_sec: float | None = None,
        interval_sec: float | None = None,
        backend_base: str | None = None,
        output_mode: str | None = None,
        disable_weather: bool = False,
    ) -> None:
        self._serial_port = serial_port
        self._serial_baud = serial_baud
        self._hid_vid = hid_vid
        self._hid_pid = hid_pid
        self._poll_sec = poll_sec
        self._interval_sec = interval_sec
        self._backend_base = backend_base
        self._output_mode = str(output_mode or "backend").strip().lower()
        self._disable_weather = bool(disable_weather)

    def build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["DATA_HANDLER_OUTPUT"] = self._output_mode if self._output_mode in ("backend", "ipc", "both") else "backend"
        if self._serial_port:
            env["SERIAL_PORT"] = self._serial_port
        if self._serial_baud:
            env["SERIAL_BAUD"] = str(self._serial_baud)
        if self._hid_vid:
            env["HID_VID"] = f"0x{self._hid_vid:04X}"
        if self._hid_pid:
            env["HID_PID"] = f"0x{self._hid_pid:04X}"
        if self._poll_sec:
            env["DATA_HANDLER_POLL_SEC"] = str(self._poll_sec)
        if self._interval_sec:
            env["DATA_HANDLER_INTERVAL_SEC"] = str(self._interval_sec)
        if self._backend_base:
            env["BACKEND_BASE"] = self._backend_base
        env["DATA_HANDLER_DISABLE_WEATHER"] = "1" if self._disable_weather else "0"
        return env

    def find_script(self) -> str:
        here = Path(__file__).resolve()
        root = here.parents[2]
        candidate = root / "data_handler_service.py"
        if candidate.exists():
            return str(candidate)
        return str(root / "data_handler" / "__main__.py")

    def python_executable(self) -> str:
        venv_python = Path(__file__).resolve().parents[1] / ".venv" / "bin" / "python"
        return str(venv_python) if venv_python.exists() else sys.executable

    def argv(self) -> list[str]:
        return [self.python_executable(), self.find_script()]
