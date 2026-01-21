from __future__ import annotations
import os
from PySide6 import QtWidgets, QtCore

from view.qt_app import MainWindow, apply_dark_palette
from controller.app_controller import AppController

# MODEL-Ports
from model.system_clock import SystemClock
from model.serial_ossd import SerialOSSD
from model.hid_sensor import HidWeatherSensor
from model.db_client import DbClient

from exception_handler import install_global_exception_hooks, format_current_exception


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

    # ---- thread-sicheres GUI-Logging (auch aus Worker-Threads) ----
    def gui_post(fn):
        try:
            QtCore.QTimer.singleShot(0, fn)
        except Exception:
            # Fallback: direkt ausführen (z.B. wenn Qt schon down ist)
            try:
                fn()
            except Exception:
                pass

    def gui_log(msg: str) -> None:
        text = str(msg)
        try:
            # Wenn wir bereits im GUI-Thread sind: direkt
            if QtCore.QThread.currentThread() == app.thread():
                win.append_log(text)
            else:
                gui_post(lambda t=text: win.append_log(t))
        except Exception:
            # letzter Fallback: stderr
            try:
                import sys
                sys.stderr.write(text + "\n")
            except Exception:
                pass

    # Global: unhandled exceptions -> Konsole + Stacktrace
    install_global_exception_hooks(log=gui_log, post=gui_post)

    # --- ENV / Defaults ---
    serial_port = os.getenv("SERIAL_PORT", "COM6")
    serial_baud = _env_int("SERIAL_BAUD", 9600)
    hid_vid     = _env_int("HID_VID", 0x1941)
    hid_pid     = _env_int("HID_PID", 0x8021)
    interval    = float(os.getenv("INTERVAL_SEC", "30"))
    base_url    = os.getenv("BACKEND_BASE", "http://127.0.0.1:8000")

    # --- MODEL-Instantiiierung ---
    clock  = SystemClock()
    db     = DbClient(base_url, log=gui_log)

    try:
        ossd = SerialOSSD(serial_port, serial_baud, clock, log=gui_log)
    except Exception as e:
        ossd = None
        gui_log(format_current_exception(f"OSSD init fehlgeschlagen: {e}"))

    try:
        weather = HidWeatherSensor(hid_vid, hid_pid, clock, log=gui_log)
    except Exception as e:
        weather = None
        gui_log(format_current_exception(f"Wettersensor init fehlgeschlagen: {e}"))

    # --- CONTROLLER ---
    ctrl = AppController(
        view=win,
        model_db=db,
        weather=weather,
        ossd=ossd,
        clock=clock,
        interval_sec=interval,
    )

    # --- VIEW-Events verbinden ---
    win.startClicked.connect(ctrl.start)
    win.stopClicked.connect(ctrl.stop)
    win.testOnceClicked.connect(ctrl.test_once)

    def _on_quit():
        try:
            ctrl.stop()
        except Exception as e:
            gui_log(format_current_exception(f"Fehler beim Stop() beim Beenden: {e}"))

    app.aboutToQuit.connect(_on_quit)
    app.exec()


if __name__ == "__main__":
    main()
