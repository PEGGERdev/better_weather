from __future__ import annotations

import unittest

from model.ipc_event_parser import IpcEventParser


class IpcEventParserTests(unittest.TestCase):
    def test_parse_ossd_event(self) -> None:
        parser = IpcEventParser()
        parsed = parser.parse_line('{"type":"ossd","ts":"2026-01-01T00:00:00+00:00","lichtgitterNr":1,"ossdNr":2,"status":"o"}')

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.kind, "ossd")
        self.assertEqual(parsed.payload.ossdStatus, "O")

    def test_parse_weather_event(self) -> None:
        parser = IpcEventParser()
        parsed = parser.parse_line('{"type":"weather","ts":"2026-01-01T00:00:00+00:00","temp":20,"pressure":1000,"light":10,"winds":1,"winddir":"NE","rain":0,"humidity":50}')

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.kind, "weather")
        self.assertEqual(parsed.payload.winddir, "NE")

    def test_non_json_line_returns_none(self) -> None:
        parser = IpcEventParser()
        self.assertIsNone(parser.parse_line("plain log line"))


if __name__ == "__main__":
    unittest.main()
