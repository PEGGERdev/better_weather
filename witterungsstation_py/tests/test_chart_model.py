from __future__ import annotations

from datetime import UTC, datetime, timedelta
import unittest

from view.chart_model import ChartDataBuffer


class ChartDataBufferTests(unittest.TestCase):
    def test_append_weather_trims_to_keep_limit(self) -> None:
        data = ChartDataBuffer(keep=2)
        base = datetime(2026, 1, 1, tzinfo=UTC)

        for offset in range(3):
            data.append_weather(
                {
                    "time": base + timedelta(minutes=offset),
                    "temp": 20 + offset,
                    "pressure": 1000 + offset,
                    "humidity": 50 + offset,
                    "light": 100 + offset,
                    "winds": 1 + offset,
                    "rain": offset,
                    "winddir": "NE",
                }
            )

        self.assertEqual(len(data.weather_x), 2)
        self.assertEqual(data.temp, [21.0, 22.0])

    def test_weather_summary_uses_nearest_sample(self) -> None:
        data = ChartDataBuffer()
        first = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        second = datetime(2026, 1, 1, 12, 10, tzinfo=UTC)
        data.append_weather({"time": first, "temp": 20, "pressure": 1000, "humidity": 40, "light": 100, "winds": 1, "rain": 0, "winddir": "N"})
        data.append_weather({"time": second, "temp": 30, "pressure": 1010, "humidity": 60, "light": 200, "winds": 2, "rain": 1, "winddir": "S"})

        summary = data.weather_summary_for(first + timedelta(minutes=8))
        self.assertIn("T=30.0C", summary)
        self.assertIn("D=S", summary)


if __name__ == "__main__":
    unittest.main()
