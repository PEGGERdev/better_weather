from __future__ import annotations

"""
Generic HID Client.

Reusable HID communication client used by data_handler and app.
"""

import os
import time
from dataclasses import dataclass
from typing import Callable, Optional, Protocol, Type


@dataclass(frozen=True)
class HidConfig:
    vid: int
    pid: int
    report_size: int = 32


class HidTransport(Protocol):
    def open(self) -> bool: ...
    def close(self) -> None: ...
    def is_open(self) -> bool: ...
    def write(self, data: bytes) -> bool: ...
    def read_chunk(self) -> bytes: ...


@dataclass(frozen=True)
class HidTransportBinding:
    name: str
    priority: int
    transport_cls: Type["BaseHidTransport"]


_TRANSPORT_REGISTRY: list[HidTransportBinding] = []


def register_hid_transport(*, name: str, priority: int) -> Callable[[Type["BaseHidTransport"]], Type["BaseHidTransport"]]:
    def decorator(transport_cls: Type["BaseHidTransport"]) -> Type["BaseHidTransport"]:
        _TRANSPORT_REGISTRY.append(
            HidTransportBinding(name=name, priority=priority, transport_cls=transport_cls)
        )
        _TRANSPORT_REGISTRY.sort(key=lambda item: item.priority)
        return transport_cls

    return decorator


def get_hid_transports() -> list[HidTransportBinding]:
    return list(_TRANSPORT_REGISTRY)


class BaseHidTransport:
    def __init__(self, config: HidConfig, log: Callable[[str], None]) -> None:
        self._config = config
        self._log = log

    def open(self) -> bool:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def is_open(self) -> bool:
        raise NotImplementedError

    def write(self, data: bytes) -> bool:
        raise NotImplementedError

    def read_chunk(self) -> bytes:
        raise NotImplementedError


@register_hid_transport(name="hidapi", priority=20)
class HidApiTransport(BaseHidTransport):
    def __init__(self, config: HidConfig, log: Callable[[str], None]) -> None:
        super().__init__(config, log)
        self._device = None

    @staticmethod
    def _iter_hidraw_paths(limit: int = 16) -> list[str]:
        return [f"/dev/hidraw{i}" for i in range(limit) if os.path.exists(f"/dev/hidraw{i}")]

    def open(self) -> bool:
        try:
            import hid
            self._device = hid.device()

            for path in self._iter_hidraw_paths():
                try:
                    idx = path.replace("/dev/hidraw", "")
                    with open(f"/sys/class/hidraw/hidraw{idx}/device/uevent", "r", encoding="utf-8") as f:
                        uevent = f.read()
                    if f"{self._config.vid:04X}" in uevent and f"{self._config.pid:04X}" in uevent:
                        self._device.open_path(path.encode())
                        self._device.set_nonblocking(True)
                        self._log(f"HID opened via hidapi path: {path}")
                        return True
                except Exception:
                    continue

            self._device.open(self._config.vid, self._config.pid)
            self._device.set_nonblocking(True)
            self._log(
                f"HID opened via hidapi VID/PID: VID=0x{self._config.vid:04X} PID=0x{self._config.pid:04X}"
            )
            return True
        except Exception as exc:
            _ = exc
            self.close()
            return False

    def close(self) -> None:
        if self._device:
            try:
                self._device.close()
            except Exception:
                pass
            self._device = None

    def is_open(self) -> bool:
        return self._device is not None

    def write(self, data: bytes) -> bool:
        if not self._device:
            return False
        try:
            return self._device.write(data) > 0
        except Exception as exc:
            self._log(f"hidapi write error: {exc}")
            return False

    def read_chunk(self) -> bytes:
        if not self._device:
            return b""
        try:
            raw = self._device.read(65)
            if not raw:
                return b""
            if len(raw) > 1:
                return bytes(raw[1:])
            return bytes(raw)
        except Exception:
            return b""


@register_hid_transport(name="hidraw", priority=10)
class HidRawTransport(BaseHidTransport):
    def __init__(self, config: HidConfig, log: Callable[[str], None]) -> None:
        super().__init__(config, log)
        self._fd: Optional[int] = None
        self._path: Optional[str] = None

    def _find_path(self) -> Optional[str]:
        for i in range(32):
            path = f"/dev/hidraw{i}"
            if not os.path.exists(path):
                continue
            try:
                with open(f"/sys/class/hidraw/hidraw{i}/device/uevent", "r", encoding="utf-8") as f:
                    text = f.read()
                vid = f"{self._config.vid:08X}"
                pid = f"{self._config.pid:08X}"
                if vid in text and pid in text:
                    return path
            except Exception:
                continue
        return None

    def open(self) -> bool:
        path = self._find_path()
        if not path:
            self._log(
                f"hidraw device not found for VID=0x{self._config.vid:04X} PID=0x{self._config.pid:04X}"
            )
            return False
        try:
            self._fd = os.open(path, os.O_RDWR | os.O_NONBLOCK)
            self._path = path
            self._log(f"HID opened via hidraw: {path}")
            return True
        except Exception as exc:
            self._log(f"hidraw open failed ({path}): {exc}")
            self.close()
            return False

    def close(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None
        self._path = None

    def is_open(self) -> bool:
        return self._fd is not None

    def write(self, data: bytes) -> bool:
        if self._fd is None:
            return False
        try:
            os.write(self._fd, data)
            return True
        except Exception as exc:
            self._log(f"hidraw write error: {exc}")
            return False

    def read_chunk(self) -> bytes:
        if self._fd is None:
            return b""
        try:
            raw = os.read(self._fd, 64)
            if not raw:
                return b""
            if raw[0] == 0 and len(raw) > 1:
                return raw[1:]
            return raw
        except BlockingIOError:
            return b""
        except Exception:
            return b""


class HidClient:
    def __init__(
        self,
        config: HidConfig,
        log: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._config = config
        self._log = log or (lambda _: None)
        self._transport: Optional[BaseHidTransport] = None
        self._transport_name: str = ""
        self._debug = os.getenv("WEATHER_DEBUG", "").strip().lower() in ("1", "true", "yes")

    def open(self) -> bool:
        for binding in get_hid_transports():
            try:
                transport = binding.transport_cls(self._config, self._log)
                if transport.open():
                    self._transport = transport
                    self._transport_name = binding.name
                    self._log(f"HID transport selected: {binding.name}")
                    return True
            except Exception as exc:
                self._log(f"HID transport init failed ({binding.name}): {exc}")
        self._log(
            f"HID open failed for all transports (VID=0x{self._config.vid:04X}, PID=0x{self._config.pid:04X})"
        )
        return False

    def close(self) -> None:
        if self._transport:
            try:
                self._transport.close()
            except Exception:
                pass
        self._transport = None
        self._transport_name = ""

    def is_open(self) -> bool:
        return self._transport is not None and self._transport.is_open()

    def write_hex(self, hex_bytes: str) -> bool:
        if not self._transport:
            return False
        parts = [p for p in hex_bytes.split() if p]
        payload = bytes(int(p, 16) & 0xFF for p in parts)
        data = bytes([0]) + payload
        try:
            return self._transport.write(data)
        except Exception as exc:
            self._log(f"HID write error: {exc}")
            return False

    def read_bytes(self, want: int, timeout: float = 1.0) -> bytes:
        if not self._transport:
            return b""
        out = bytearray()
        end = time.time() + timeout
        while len(out) < want and time.time() < end:
            try:
                raw = self._transport.read_chunk()
                if raw:
                    out.extend(raw)
                else:
                    time.sleep(0.02)
            except Exception:
                time.sleep(0.02)
        return bytes(out[:want])

    def drain_input(self, max_wait: float = 0.08) -> None:
        if not self._transport:
            return
        end = time.time() + max(0.0, float(max_wait))
        while time.time() < end:
            try:
                raw = self._transport.read_chunk()
                if not raw:
                    break
            except Exception:
                break

    def query(self, command_hex: str, response_size: int, timeout: float = 1.0) -> Optional[bytes]:
        self.drain_input()
        if not self.write_hex(command_hex):
            return None
        time.sleep(0.02)
        return self.read_bytes(response_size, timeout)

    def debug_log(self, message: str) -> None:
        if self._debug:
            self._log(f"[HID DEBUG] {message}")

    def __enter__(self) -> "HidClient":
        self.open()
        return self

    def __exit__(self, *args) -> None:
        self.close()
