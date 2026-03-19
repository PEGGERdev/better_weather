from __future__ import annotations

"""
Witterungstester – Main (Composition Root)

Role
- Wires the legacy registry-driven GUI runtime (controller/services/view).
- Connects Qt signals and installs global exception hooks.

Status
- Legacy compatibility runtime. First-class product runtime is backend + web frontend.

Design
- Keep composition here (DIP), keep business logic inside controller/model.
"""

from PySide6 import QtWidgets, QtCore

from bootstrap.app_bootstrap import build_gui_context
from view.qt_app import MainWindow, apply_dark_palette

from exception_handler import install_global_exception_hooks, format_current_exception


class _GuiInvoker(QtCore.QObject):
    invoke = QtCore.Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.invoke.connect(self._run, QtCore.Qt.ConnectionType.QueuedConnection)

    @QtCore.Slot(object)
    def _run(self, fn) -> None:
        fn()


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
        self._invoker = _GuiInvoker()

    def post(self, fn) -> None:
        try:
            if QtCore.QThread.currentThread() == self._app.thread():
                fn()
            else:
                self._invoker.invoke.emit(fn)
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

    # ---------------- runtime context ----------------
    ctx = build_gui_context(view=win, log=gui.log, post=gui.post)
    ctrl = ctx.controller("app")

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
