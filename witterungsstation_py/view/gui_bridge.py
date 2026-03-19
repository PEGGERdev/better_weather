from __future__ import annotations

try:
    from PySide6 import QtCore

    _HAS_QT = True
except Exception:  # pragma: no cover
    QtCore = None
    _HAS_QT = False


class GuiBridge:
    def post(self, fn) -> None:
        try:
            if _HAS_QT and QtCore is not None:
                QtCore.QTimer.singleShot(0, fn)
            else:
                fn()
        except Exception:
            try:
                fn()
            except Exception:
                pass
