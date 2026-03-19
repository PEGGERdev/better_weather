# view/qt_app.py
from __future__ import annotations

"""
Witterungstester – Qt View (PySide6)

Role
- UI: LEDs for OSSD, labels/table for current weather, chart for trends/events.

Interfaces (used by controller)
- update_ossd(state)
- update_weather(payload)
- chart_add_ossd(...)
- chart_redraw()
- append_log(...)

Threading
- Must be executed on the GUI thread only.
"""

from typing import Tuple
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from view.chart_model import ChartDataBuffer
from view.chart_renderer import WeatherChartRenderer
from view.runtime_components import get_weather_fields


# ---------------- Dark theme ----------------
def apply_dark_palette(app: QtWidgets.QApplication) -> None:
    palette = QtGui.QPalette()
    c_bg = QtGui.QColor(37, 37, 39)
    c_mid = QtGui.QColor(53, 53, 55)
    c_fg = QtGui.QColor(220, 220, 220)
    c_acc = QtGui.QColor(42, 130, 218)

    palette.setColor(QtGui.QPalette.ColorRole.Window, c_bg)
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, c_fg)
    palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(30, 30, 30))
    palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, c_mid)
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, c_fg)
    palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, c_fg)
    palette.setColor(QtGui.QPalette.ColorRole.Text, c_fg)
    palette.setColor(QtGui.QPalette.ColorRole.Button, c_mid)
    palette.setColor(QtGui.QPalette.ColorRole.ButtonText, c_fg)
    palette.setColor(QtGui.QPalette.ColorRole.Highlight, c_acc)
    palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(0, 0, 0))
    app.setPalette(palette)
    app.setStyle("Fusion")


# ---------------- small LED widget ----------------
class Led(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 20)
        self._set(False)

    def _set(self, on: bool):
        # NOTE: KISS – only two states: OK(green) / Error(red)
        col = "#7a3a3a" if not on else "#2e7d32"
        self.setStyleSheet(f"QFrame {{ background: {col}; border-radius: 6px; border: 1px solid #444; }}")


class MainWindow(QtWidgets.QMainWindow):
    startClicked = QtCore.Signal()
    stopClicked = QtCore.Signal()
    testOnceClicked = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Witterungstester – Python")
        self.resize(1000, 640)

        # ---------------- toolbar ----------------
        tb = self.addToolBar("main")
        tb.setMovable(False)
        act_start = tb.addAction("Start")
        act_stop = tb.addAction("Stop")
        act_test1 = tb.addAction("Test 1×")
        act_start.triggered.connect(self.startClicked.emit)
        act_stop.triggered.connect(self.stopClicked.emit)
        act_test1.triggered.connect(self.testOnceClicked.emit)

        # ---------------- header LEDs ----------------
        header = QtWidgets.QGroupBox("OSSD Status (Gesamt)")
        grid = QtWidgets.QGridLayout(header)
        self._leds = [Led(), Led(), Led(), Led()]
        labels = ["LG1 OSSD1", "LG1 OSSD2", "LG2 OSSD1", "LG2 OSSD2"]
        for i, (txt, led) in enumerate(zip(labels, self._leds)):
            v = QtWidgets.QVBoxLayout()
            v.addWidget(QtWidgets.QLabel(txt), alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
            v.addWidget(led, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
            grid.addLayout(v, 0, i)

        # ---------------- tabs ----------------
        tabs = QtWidgets.QTabWidget()

        # Overview
        self._tab_over = QtWidgets.QWidget()
        lo = QtWidgets.QGridLayout(self._tab_over)

        left = QtWidgets.QGroupBox("Direkt (Hardware)")
        gl = QtWidgets.QFormLayout(left)
        self._weather_labels: dict[str, QtWidgets.QLabel] = {}
        self._weather_fields = get_weather_fields()
        for field in self._weather_fields:
            widget = QtWidgets.QLabel("…")
            self._weather_labels[field.id] = widget
            gl.addRow(field.title, widget)

        right = QtWidgets.QGroupBox("Von Datenbank")
        self._right_dummy = QtWidgets.QLabel("…")
        fr = QtWidgets.QVBoxLayout(right)
        self._telemetry_mode_label = QtWidgets.QLabel("Telemetry-Modus: Unbekannt")
        self._telemetry_mode_label.setStyleSheet("color: #93c5fd; font-weight: 600;")
        fr.addWidget(self._telemetry_mode_label)
        fr.addWidget(self._right_dummy)

        lo.addWidget(left, 0, 0)
        lo.addWidget(right, 0, 1)

        tabs.addTab(self._tab_over, "Übersicht")

        # Console
        self._txt_console = QtWidgets.QPlainTextEdit()
        self._txt_console.setReadOnly(True)
        tabs.addTab(self._txt_console, "Konsole")

        # Chart (matplotlib)
        self._fig = Figure(figsize=(8, 5), constrained_layout=True)
        self._canvas = FigureCanvas(self._fig)

        self._chart_data = ChartDataBuffer()
        self._chart = WeatherChartRenderer(self._fig)
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)

        tabs.addTab(self._canvas, "Diagramm")

        # ---------------- central layout ----------------
        central = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(central)
        lay.addWidget(header)
        lay.addWidget(tabs)
        self.setCentralWidget(central)

        # Statusbar
        self.statusBar().showMessage("Bereit")

    # ---------------- public API (used by controller) ----------------
    @QtCore.Slot()
    def set_running_state(self, running: bool) -> None:
        self.statusBar().showMessage("Läuft…" if running else "Bereit")

    @QtCore.Slot()
    def set_status(self, text: str) -> None:
        self.statusBar().showMessage(text)

    @QtCore.Slot()
    def show_error(self, msg: str) -> None:
        self.append_log(f"Fehler: {msg}")

    @QtCore.Slot()
    def set_telemetry_mode(self, text: str) -> None:
        self._telemetry_mode_label.setText(f"Telemetry-Modus: {text}")
        self.statusBar().showMessage(f"Bereit - {text}" if not self._txt_console.hasFocus() else self.statusBar().currentMessage())

    @QtCore.Slot()
    def append_log(self, line: str) -> None:
        self._txt_console.appendPlainText(str(line))

    # Backwards-compatible alias
    append_console = append_log

    @QtCore.Slot()
    def update_weather(self, payload: dict) -> None:
        """
        Updates the "table/labels" (always current).
        Chart data is only buffered here (no redraw).
        """
        def _fmt(v, unit=""):
            return "…" if v is None else f"{v}{unit}"

        for field in self._weather_fields:
            label = self._weather_labels.get(field.id)
            if not label:
                continue
            raw_value = payload.get(field.payload_key)
            if field.payload_key == "pressure" and raw_value is None:
                raw_value = payload.get("pressure")
            if field.id == "winddir":
                label.setText(str(raw_value or "…"))
            else:
                label.setText(_fmt(raw_value, field.unit))

        timestamp = payload.get("time")
        ts_text = timestamp.strftime("%H:%M:%S") if hasattr(timestamp, "strftime") else "-"
        self._right_dummy.setText(
            "\n".join(
                (
                    f"Letzte Live-Daten: {ts_text}",
                    f"Temp {self._weather_labels['temp'].text()}",
                    f"Druck {self._weather_labels['pressure'].text()}",
                    f"Feuchte {self._weather_labels['humidity'].text()}",
                    f"Wind {self._weather_labels['winds'].text()} {self._weather_labels['winddir'].text()}",
                    f"Regen {self._weather_labels['rain'].text()}",
                    f"Licht {self._weather_labels['light'].text()}",
                )
            )
        )

        self._chart_data.append_weather(payload)

    @QtCore.Slot()
    def update_ossd(self, st: Tuple[bool, bool, bool, bool]) -> None:
        """Updates LEDs live."""
        for i, val in enumerate(st):
            self._leds[i]._set(bool(val))

    @QtCore.Slot()
    def chart_add_ossd(self, channel_idx: int, ts: datetime, label: str) -> None:
        """
        Buffers OSSD events for the chart.
        Redraw happens only on interval via chart_redraw().
        """
        self._chart_data.append_ossd(channel_idx, ts, label)

    @QtCore.Slot()
    def chart_redraw(self) -> None:
        """
        Redraws chart from buffers.
        Called by controller only on interval (performance).
        """
        self._chart.redraw(self._chart_data)

    # ---------------- matplotlib hover ----------------
    def _on_hover(self, event):
        self._chart.handle_hover(event, self._chart_data)
