from __future__ import annotations
import os
from PySide6 import QtWidgets

from view.qt_app import MainWindow, apply_dark_palette
from controller.app_controller import AppController

# MODEL-Ports
from model.system_clock import SystemClock
from model.serial_ossd import SerialOSSD
from model.hid_sensor import HidWeatherSensor
from model.db_client import DbClient


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    try:
        if v and v.lower().startswith("0x"):
            return int(v, 16)
        return int(v) if v is not None else default
    except Exception:
        return default


def main() -> None:
    app = QtWidgets.QApplication([])
    apply_dark_palette(app)

    win = MainWindow()
    win.show()

    # --- ENV / Defaults ---
    serial_port = os.getenv("SERIAL_PORT", "COM6")
    serial_baud = _env_int("SERIAL_BAUD", 9600)
    hid_vid     = _env_int("HID_VID", 0x1941)
    hid_pid     = _env_int("HID_PID", 0x8021)
    interval    = float(os.getenv("INTERVAL_SEC", "30"))
    base_url    = os.getenv("BACKEND_BASE", "http://127.0.0.1:8000")

    # --- MODEL-Instantiiierung ---
    clock  = SystemClock()
    db     = DbClient(base_url, log=win.append_log)

    try:
        ossd = SerialOSSD(serial_port, serial_baud, clock, log=win.append_log)
    except Exception as e:
        ossd = None
        win.append_log(f"OSSD init fehlgeschlagen: {e}")

    try:
        weather = HidWeatherSensor(hid_vid, hid_pid, clock)
    except Exception as e:
        weather = None
        win.append_log(f"Wettersensor init fehlgeschlagen: {e}")

    # --- CONTROLLER ---
    ctrl = AppController(view=win, model_db=db, weather=weather, ossd=ossd, clock=clock, interval_sec=interval)

    # --- VIEW-Events verbinden ---
    win.startClicked.connect(ctrl.start)
    win.stopClicked.connect(ctrl.stop)
    win.testOnceClicked.connect(ctrl.test_once)

    def _on_quit():
        try:
            ctrl.stop()
        except Exception:
            pass

    app.aboutToQuit.connect(_on_quit)
    app.exec()


if __name__ == "__main__":
    main()
