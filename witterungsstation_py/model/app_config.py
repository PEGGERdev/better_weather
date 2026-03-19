from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import env_float, env_int, env_str

@dataclass(frozen=True)
class RuntimeConfig:
    serial_port: str
    serial_baud: int
    hid_vid: int
    hid_pid: int
    interval_sec: float
    poll_sec: float
    backend_base: str


def load_runtime_config() -> RuntimeConfig:
    return RuntimeConfig(
        serial_port=env_str("SERIAL_PORT", "/dev/ttyACM0"),
        serial_baud=env_int("SERIAL_BAUD", 9600),
        hid_vid=env_int("HID_VID", 0x1941),
        hid_pid=env_int("HID_PID", 0x8021),
        interval_sec=env_float("INTERVAL_SEC", 30.0),
        poll_sec=env_float("POLL_SEC", 0.2),
        backend_base=env_str("BACKEND_BASE", "http://127.0.0.1:8000"),
    )
