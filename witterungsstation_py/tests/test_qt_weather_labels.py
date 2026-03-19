from __future__ import annotations

from datetime import UTC, datetime
import unittest

from PySide6 import QtWidgets

from view.qt_app import MainWindow


class QtWeatherLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_update_weather_updates_labels_and_prints_values(self) -> None:
        win = MainWindow()
        payload = {
            "temp": 21.5,
            "pressure": 1009.3,
            "light": 456.0,
            "winds": 1.8,
            "winddir": "NW",
            "rain": 0.6,
            "humidity": 63.0,
            "time": datetime(2026, 3, 11, 14, 0, tzinfo=UTC),
        }

        win.update_weather(payload)

        values = {field_id: label.text() for field_id, label in win._weather_labels.items()}
        print("payload:", payload)
        print("label values:", values)

        self.assertEqual(values["temp"], "21.5 °C")
        self.assertEqual(values["pressure"], "1009.3 hPa")
        self.assertEqual(values["light"], "456.0")
        self.assertEqual(values["winds"], "1.8 km/h")
        self.assertEqual(values["winddir"], "NW")
        self.assertEqual(values["rain"], "0.6 mm")
        self.assertEqual(values["humidity"], "63.0 %")

        win.close()


if __name__ == "__main__":
    unittest.main()
