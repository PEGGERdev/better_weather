from __future__ import annotations

import json
import os
import unittest
from typing import cast

from shared.config import load_data_handler_config
from data_handler.contracts import BaseOutputHandler
from data_handler.core import IpcOutputHandler, BackendOutputHandler
from data_handler.outputs.composite_output import CompositeOutputHandler
from datetime import UTC, datetime


class FakeLog:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, msg: str) -> None:
        self.lines.append(msg)


class DataHandlerConfigTests(unittest.TestCase):
    def test_load_config_defaults(self) -> None:
        old = {k: os.environ.get(k) for k in (
            "SERIAL_PORT", "SERIAL_BAUD", "HID_VID", "HID_PID",
            "DATA_HANDLER_POLL_SEC", "DATA_HANDLER_INTERVAL_SEC",
            "BACKEND_BASE", "DATA_HANDLER_OUTPUT", "LOG_LEVEL",
        )}
        try:
            for k in old:
                os.environ.pop(k, None)
            cfg = load_data_handler_config()
            self.assertEqual(cfg.serial.port, "/dev/ttyACM0")
            self.assertEqual(cfg.serial.baud, 9600)
            self.assertEqual(cfg.hid.vid, 0x1941)
            self.assertEqual(cfg.hid.pid, 0x8021)
            self.assertEqual(cfg.output_mode, "backend")
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_load_config_ipc_mode(self) -> None:
        old = os.environ.get("DATA_HANDLER_OUTPUT")
        try:
            os.environ["DATA_HANDLER_OUTPUT"] = "ipc"
            cfg = load_data_handler_config()
            self.assertEqual(cfg.output_mode, "ipc")
        finally:
            if old is None:
                os.environ.pop("DATA_HANDLER_OUTPUT", None)
            else:
                os.environ["DATA_HANDLER_OUTPUT"] = old

    def test_load_config_both_mode(self) -> None:
        old = os.environ.get("DATA_HANDLER_OUTPUT")
        try:
            os.environ["DATA_HANDLER_OUTPUT"] = "both"
            cfg = load_data_handler_config()
            self.assertEqual(cfg.output_mode, "both")
        finally:
            if old is None:
                os.environ.pop("DATA_HANDLER_OUTPUT", None)
            else:
                os.environ["DATA_HANDLER_OUTPUT"] = old


class IpcOutputHandlerTests(unittest.TestCase):
    def test_emit_ossd_outputs_json(self) -> None:
        import io
        import sys

        fake_stdout = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = fake_stdout
            log = FakeLog()
            handler = IpcOutputHandler(log)
            ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
            handler.emit_ossd(ts, 1, 2, "E")
            output = fake_stdout.getvalue().strip()
            obj = json.loads(output)
            self.assertEqual(obj["type"], "ossd")
            self.assertEqual(obj["lichtgitterNr"], 1)
            self.assertEqual(obj["ossdNr"], 2)
            self.assertEqual(obj["status"], "E")
        finally:
            sys.stdout = old_stdout

    def test_emit_weather_outputs_json(self) -> None:
        import io
        import sys

        fake_stdout = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = fake_stdout
            log = FakeLog()
            handler = IpcOutputHandler(log)
            ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
            handler.emit_weather(
                ts=ts,
                temp=18.5,
                pressure=1008.2,
                humidity=56.0,
                winds=2.7,
                winddir="SW",
                rain=0.0,
                light=420.0,
            )
            output = fake_stdout.getvalue().strip()
            obj = json.loads(output)
            self.assertEqual(obj["type"], "weather")
            self.assertEqual(obj["temp"], 18.5)
            self.assertEqual(obj["pressure"], 1008.2)
            self.assertEqual(obj["winddir"], "SW")
        finally:
            sys.stdout = old_stdout


class CompositeOutputHandlerTests(unittest.TestCase):
    def test_emits_to_all_children(self) -> None:
        class FakeOutput(BaseOutputHandler):
            def __init__(self) -> None:
                self.calls: list[tuple[str, tuple]] = []

            def emit_ossd(self, ts, lichtgitter_nr, ossd_nr, status) -> None:
                self.calls.append(("ossd", (ts, lichtgitter_nr, ossd_nr, status)))

            def emit_weather(self, ts, temp, pressure, humidity, winds, winddir, rain, light) -> None:
                self.calls.append(("weather", (ts, temp, pressure, humidity, winds, winddir, rain, light)))

            def close(self) -> None:
                self.calls.append(("close", ()))

        left = FakeOutput()
        right = FakeOutput()
        handler = CompositeOutputHandler(cast(BaseOutputHandler, left), cast(BaseOutputHandler, right))
        ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

        handler.emit_ossd(ts, 1, 2, "E")
        handler.emit_weather(ts, 18.5, 1008.2, 56.0, 2.7, "SW", 0.0, 420.0)
        handler.close()

        self.assertEqual(len(left.calls), 3)
        self.assertEqual(len(right.calls), 3)


if __name__ == "__main__":
    unittest.main()
