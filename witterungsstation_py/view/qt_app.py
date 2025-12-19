from __future__ import annotations
from typing import Any, Tuple
from datetime import datetime

from PySide6 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# -------- Dark theme ----------
def apply_dark_palette(app: QtWidgets.QApplication) -> None:
    palette = QtGui.QPalette()
    c_bg = QtGui.QColor(37, 37, 39)
    c_mid = QtGui.QColor(53, 53, 55)
    c_fg = QtGui.QColor(220, 220, 220)
    c_acc = QtGui.QColor(42, 130, 218)

    palette.setColor(QtGui.QPalette.Window, c_bg)
    palette.setColor(QtGui.QPalette.WindowText, c_fg)
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(30, 30, 30))
    palette.setColor(QtGui.QPalette.AlternateBase, c_mid)
    palette.setColor(QtGui.QPalette.ToolTipBase, c_fg)
    palette.setColor(QtGui.QPalette.ToolTipText, c_fg)
    palette.setColor(QtGui.QPalette.Text, c_fg)
    palette.setColor(QtGui.QPalette.Button, c_mid)
    palette.setColor(QtGui.QPalette.ButtonText, c_fg)
    palette.setColor(QtGui.QPalette.Highlight, c_acc)
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(0, 0, 0))
    app.setPalette(palette)
    app.setStyle("Fusion")


# -------- kleine LED ----------
class Led(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 20)
        self._set(False)

    def _set(self, on: bool):
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

        # Toolbar
        tb = self.addToolBar("main")
        tb.setMovable(False)
        act_start = tb.addAction("Start")
        act_stop  = tb.addAction("Stop")
        act_test1 = tb.addAction("Test 1×")
        act_start.triggered.connect(self.startClicked.emit)
        act_stop.triggered.connect(self.stopClicked.emit)
        act_test1.triggered.connect(self.testOnceClicked.emit)

        # Header: OSSD LEDs
        header = QtWidgets.QGroupBox("OSSD Status (Gesamt)")
        grid = QtWidgets.QGridLayout(header)
        self._leds = [Led(), Led(), Led(), Led()]
        labels = ["LG1 OSSD1", "LG1 OSSD2", "LG2 OSSD1", "LG2 OSSD2"]
        for i, (txt, led) in enumerate(zip(labels, self._leds)):
            v = QtWidgets.QVBoxLayout()
            v.addWidget(QtWidgets.QLabel(txt), alignment=QtCore.Qt.AlignHCenter)
            v.addWidget(led, alignment=QtCore.Qt.AlignHCenter)
            grid.addLayout(v, 0, i)

        # Tabs
        tabs = QtWidgets.QTabWidget()
        # Übersicht
        self._tab_over = QtWidgets.QWidget()
        lo = QtWidgets.QGridLayout(self._tab_over)

        self.lbl_temp_hw = QtWidgets.QLabel("…")
        self.lbl_press_hw = QtWidgets.QLabel("…")
        self.lbl_light_hw = QtWidgets.QLabel("…")
        self.lbl_winds_hw = QtWidgets.QLabel("…")
        self.lbl_winddir_hw = QtWidgets.QLabel("…")
        self.lbl_rain_hw = QtWidgets.QLabel("…")
        self.lbl_humi_hw = QtWidgets.QLabel("…")

        left = QtWidgets.QGroupBox("Direkt (Hardware)")
        gl = QtWidgets.QFormLayout(left)
        gl.addRow("Temp:", self.lbl_temp_hw)
        gl.addRow("Luftdruck:", self.lbl_press_hw)
        gl.addRow("Lichteinstrahlung:", self.lbl_light_hw)
        gl.addRow("Windgeschw.:", self.lbl_winds_hw)
        gl.addRow("Windrichtung:", self.lbl_winddir_hw)
        gl.addRow("Regen:", self.lbl_rain_hw)
        gl.addRow("Luftfeuchte:", self.lbl_humi_hw)

        right = QtWidgets.QGroupBox("Von Datenbank")
        self._right_dummy = QtWidgets.QLabel("…")
        fr = QtWidgets.QVBoxLayout(right)
        fr.addWidget(self._right_dummy)

        lo.addWidget(left, 0, 0)
        lo.addWidget(right, 0, 1)

        tabs.addTab(self._tab_over, "Übersicht")

        # Konsole
        self._txt_console = QtWidgets.QPlainTextEdit()
        self._txt_console.setReadOnly(True)
        tabs.addTab(self._txt_console, "Konsole")

        # Diagramm (matplotlib)
        fig = Figure(figsize=(5, 3), constrained_layout=True)
        self._ax_w = fig.add_subplot(111)
        self._ax_w.set_title("Wetter & OSSD")
        self._ax_w.set_xlabel("Zeit")
        self._ax_w.set_ylabel("Temp [°C]")
        self._ax_w.grid(True, alpha=0.25)
        self._canvas = FigureCanvas(fig)

        self._scatter = self._ax_w.scatter([], [], marker='x', s=60, linewidths=1.5)  # OSSD-Events
        self._hover_ann = self._ax_w.annotate("", xy=(0,0), xytext=(15,15),
                                              textcoords="offset points",
                                              bbox=dict(boxstyle="round", fc="w", ec="0.5", alpha=0.9),
                                              arrowprops=dict(arrowstyle="->"))
        self._hover_ann.set_visible(False)
        self._canvas.mpl_connect("motion_notify_event", self._on_hover)

        tabs.addTab(self._canvas, "Diagramm")

        # Central
        central = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(central)
        lay.addWidget(header)
        lay.addWidget(tabs)
        self.setCentralWidget(central)

        # Statusbar
        self.statusBar().showMessage("Bereit")

        # Daten für Plot
        self._x_temp: list[datetime] = []
        self._y_temp: list[float] = []
        self._ossd_x: list[datetime] = []
        self._ossd_y: list[float] = []
        self._ossd_label: list[str] = []

    # ------------- public API (vom Controller genutzt) -------------
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
    def append_log(self, line: str) -> None:
        self._txt_console.appendPlainText(str(line))

    # Alias für alte Aufrufe (Kompatibilität)
    append_console = append_log

    @QtCore.Slot()
    def update_weather(self, payload: dict) -> None:
        def _fmt(v, unit=""):
            return "…" if v is None else f"{v}{unit}"
        self.lbl_temp_hw.setText(_fmt(payload.get("temp"), " °C"))
        self.lbl_press_hw.setText(_fmt(payload.get("preassure"), " hPa"))
        self.lbl_light_hw.setText(_fmt(payload.get("light")))
        self.lbl_winds_hw.setText(_fmt(payload.get("winds"), " m/s"))
        self.lbl_winddir_hw.setText(payload.get("winddir") or "…")
        self.lbl_rain_hw.setText(_fmt(payload.get("rain"), " mm"))
        self.lbl_humi_hw.setText(_fmt(payload.get("humidity"), " %"))

        # Plot Temperaturverlauf
        t: datetime = payload.get("time")
        temp = payload.get("temp")
        if t and temp is not None:
            self._x_temp.append(t)
            self._y_temp.append(temp)
            self._ax_w.plot(self._x_temp, self._y_temp, linewidth=1.0)  # keine Farbe setzen
            self._canvas.draw_idle()

    @QtCore.Slot()
    def update_ossd(self, st: Tuple[bool, bool, bool, bool]) -> None:
        for i, val in enumerate(st):
            self._leds[i]._set(bool(val))

    # Diagramm: OSSD-Event mit Marker "X" + Hover-Text
    @QtCore.Slot()
    def chart_add_ossd(self, channel_idx: int, ts: datetime, label: str) -> None:
        # y-Level je Kanal (optisch getrennt)
        base = {0: 0.2, 1: 0.4, 2: 0.6, 3: 0.8}[channel_idx]
        self._ossd_x.append(ts)
        self._ossd_y.append(base)
        self._ossd_label.append(label)
        self._scatter.remove()
        self._scatter = self._ax_w.scatter(self._ossd_x, self._ossd_y, marker='x', s=70, linewidths=1.8)
        self._canvas.draw_idle()

    # Matplotlib Hover
    def _on_hover(self, event):
        vis = self._hover_ann.get_visible()
        if event.inaxes == self._ax_w and self._ossd_x:
            cont, ind = self._scatter.contains(event)
            if cont:
                idx = ind["ind"][0]
                x = self._ossd_x[idx]
                y = self._ossd_y[idx]
                self._hover_ann.xy = (x, y)
                self._hover_ann.set_text(self._ossd_label[idx])
                self._hover_ann.set_visible(True)
                self._canvas.draw_idle()
                return
        if vis:
            self._hover_ann.set_visible(False)
            self._canvas.draw_idle()
