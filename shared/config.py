from __future__ import annotations

"""
Shared configuration service.

Centralized configuration loading used by backend, data_handler, and frontend.
"""

import os
from dataclasses import dataclass
from typing import Literal, Optional


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    try:
        if value and value.lower().startswith("0x"):
            return int(value, 16)
        return int(value) if value is not None else default
    except Exception:
        return default


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    try:
        return float(value) if value is not None else default
    except Exception:
        return default


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "y", "on")


def env_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value.strip() if value is not None else default


@dataclass(frozen=True)
class SerialConfig:
    port: str
    baud: int


@dataclass(frozen=True)
class HidConfig:
    vid: int
    pid: int


@dataclass(frozen=True)
class BackendConfig:
    base_url: str


@dataclass(frozen=True)
class MongoConfig:
    url: str
    database: str


@dataclass(frozen=True)
class LoggingConfig:
    level: str


@dataclass(frozen=True)
class DataHandlerConfig:
    serial: SerialConfig
    hid: HidConfig
    backend: BackendConfig
    poll_sec: float
    interval_sec: float
    output_mode: Literal["backend", "ipc", "both"]
    disable_weather: bool
    logging: LoggingConfig


@dataclass(frozen=True)
class AppConfig:
    serial: SerialConfig
    hid: HidConfig
    backend: BackendConfig
    mongo: MongoConfig
    interval_sec: float
    poll_sec: float
    logging: LoggingConfig


def load_serial_config() -> SerialConfig:
    return SerialConfig(
        port=env_str("SERIAL_PORT", "/dev/ttyACM0"),
        baud=env_int("SERIAL_BAUD", 9600),
    )


def load_hid_config() -> HidConfig:
    return HidConfig(
        vid=env_int("HID_VID", 0x1941),
        pid=env_int("HID_PID", 0x8021),
    )


def load_backend_config() -> BackendConfig:
    return BackendConfig(
        base_url=env_str("BACKEND_BASE", "http://127.0.0.1:8000"),
    )


def load_mongo_config() -> MongoConfig:
    return MongoConfig(
        url=env_str("MONGO_URL", "mongodb://localhost:27017"),
        database=env_str("MONGO_DATABASE", "witterungsstation"),
    )


def load_logging_config() -> LoggingConfig:
    return LoggingConfig(
        level=env_str("LOG_LEVEL", "INFO").upper(),
    )


def load_data_handler_config() -> DataHandlerConfig:
    output_mode_raw = env_str("DATA_HANDLER_OUTPUT", "backend").lower()
    if output_mode_raw not in ("backend", "ipc", "both"):
        output_mode_raw = "backend"

    return DataHandlerConfig(
        serial=load_serial_config(),
        hid=load_hid_config(),
        backend=load_backend_config(),
        poll_sec=env_float("DATA_HANDLER_POLL_SEC", 0.2),
        interval_sec=env_float("DATA_HANDLER_INTERVAL_SEC", 30.0),
        output_mode=output_mode_raw,
        disable_weather=env_bool("DATA_HANDLER_DISABLE_WEATHER", False),
        logging=load_logging_config(),
    )


def load_app_config() -> AppConfig:
    return AppConfig(
        serial=load_serial_config(),
        hid=load_hid_config(),
        backend=load_backend_config(),
        mongo=load_mongo_config(),
        interval_sec=env_float("INTERVAL_SEC", 30.0),
        poll_sec=env_float("POLL_SEC", 0.2),
        logging=load_logging_config(),
    )
