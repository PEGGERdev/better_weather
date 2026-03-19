from __future__ import annotations

import unittest

from model.data_handler_command import DataHandlerCommand


class DataHandlerCommandTests(unittest.TestCase):
    def test_build_env_maps_runtime_inputs(self) -> None:
        command = DataHandlerCommand(
            serial_port="/dev/ttyACM9",
            serial_baud=115200,
            hid_vid=0x1941,
            hid_pid=0x8021,
            poll_sec=0.5,
            interval_sec=30.0,
            backend_base="http://127.0.0.1:8000",
            output_mode="ipc",
            disable_weather=True,
        )

        env = command.build_env()
        self.assertEqual(env["SERIAL_PORT"], "/dev/ttyACM9")
        self.assertEqual(env["SERIAL_BAUD"], "115200")
        self.assertEqual(env["HID_VID"], "0x1941")
        self.assertEqual(env["HID_PID"], "0x8021")
        self.assertEqual(env["DATA_HANDLER_OUTPUT"], "ipc")
        self.assertEqual(env["DATA_HANDLER_DISABLE_WEATHER"], "1")

    def test_build_env_preserves_both_output_mode(self) -> None:
        command = DataHandlerCommand(output_mode="both")

        env = command.build_env()
        self.assertEqual(env["DATA_HANDLER_OUTPUT"], "both")


if __name__ == "__main__":
    unittest.main()
