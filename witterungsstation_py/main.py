from __future__ import annotations

"""
Witterungstester – Main (Composition Root)

Role
- Wires concrete implementations (Clock, SerialOSSD, HidWeatherSensor, DbClient, Controller, View).
- Connects Qt signals and installs global exception hooks.

Design
- Keep composition here (DIP), keep business logic inside controller/model.
"""

import os
from PySide6 import QtWidgets, QtCore

from view.qt_app import MainWindow, apply_dark_palette
from controller.app_controller import AppController

from model.system_clock import SystemClock
from model.serial_ossd import SerialOSSD
from model.hid_sensor import HidWeatherSensor
from model.db_client import DbClient

from exception_handler import install_global_exception_hooks, format_current_exception


def _env_int(name: str, default: int) -> int:
    """
    Helper: read an int from ENV.
    Supports decimal and 0x.. (hex).
    """
    v = os.getenv(name)
    try:
        if v and v.lower().startswith("0x"):
            return int(v, 16)
        return int(v) if v is not None else default
    except Exception:
        return default


class GuiDispatch:
    """
    Thread-safe GUI dispatcher for:
    - posting callables onto the GUI thread
    - logging from any thread into the GUI console

    WHY
    - Worker threads must not touch Qt widgets directly.
    """

    def __init__(self, app: QtWidgets.QApplication, win: MainWindow) -> None:
        self._app = app
        self._win = win

    def post(self, fn) -> None:
        try:
            QtCore.QTimer.singleShot(0, fn)
        except Exception:
            # Last-resort fallback: execute directly (Qt may be shutting down)
            try:
                fn()
            except Exception:
                pass

    def log(self, msg: str) -> None:
        text = str(msg)
        try:
            if QtCore.QThread.currentThread() == self._app.thread():
                self._win.append_log(text)
            else:
                self.post(lambda t=text: self._win.append_log(t))
        except Exception:
            try:
                import sys
                sys.stderr.write(text + "\n")
            except Exception:
                pass


def main() -> None:
    # ---------------- Qt bootstrap ----------------
    app = QtWidgets.QApplication([])
    apply_dark_palette(app)

    win = MainWindow()
    win.show()

    gui = GuiDispatch(app, win)

    # Global: unhandled exceptions -> GUI console + full traceback
    install_global_exception_hooks(log=gui.log, post=gui.post)

    # ---------------- ENV / defaults ----------------
    serial_port = os.getenv("SERIAL_PORT", "COM6")
    serial_baud = _env_int("SERIAL_BAUD", 9600)
    hid_vid = _env_int("HID_VID", 0x1941)
    hid_pid = _env_int("HID_PID", 0x8021)
    interval = float(os.getenv("INTERVAL_SEC", "30"))
    poll_sec = float(os.getenv("POLL_SEC", "0.2"))
    base_url = os.getenv("BACKEND_BASE", "http://127.0.0.1:8000")

    # ---------------- model wiring ----------------
    clock = SystemClock()
    db = DbClient(base_url, log=gui.log)

    # NOTE: Hardware adapters are optional; app should still start without them.
    try:
        ossd = SerialOSSD(serial_port, serial_baud, clock, log=gui.log)
    except Exception as e:
        ossd = None
        gui.log(format_current_exception(f"OSSD init failed: {e}"))

    try:
        weather = HidWeatherSensor(hid_vid, hid_pid, clock, log=gui.log)
    except Exception as e:
        weather = None
        gui.log(format_current_exception(f"Weather sensor init failed: {e}"))

    # ---------------- controller ----------------
    ctrl = AppController(
        view=win,
        model_db=db,
        weather=weather,
        ossd=ossd,
        clock=clock,
        interval_sec=interval,
        poll_sec=poll_sec,
    )

    # ---------------- view events ----------------
    win.startClicked.connect(ctrl.start)
    win.stopClicked.connect(ctrl.stop)
    win.testOnceClicked.connect(ctrl.test_once)

    def _on_quit():
        try:
            ctrl.stop()
        except Exception as e:
            gui.log(format_current_exception(f"Error during stop() on shutdown: {e}"))

    app.aboutToQuit.connect(_on_quit)
    app.exec()


if __name__ == "__main__":
    main()
