from __future__ import annotations

import unittest

from shared.parser_registry import get_parsers, get_parser_by_name, get_parser_by_data_type
from shared.parsers import OssdParser, WeatherParser


class ParserRegistryTests(unittest.TestCase):
    def test_parsers_are_registered(self) -> None:
        parsers = get_parsers()
        names = [p.name for p in parsers]
        self.assertIn("ossd", names)
        self.assertIn("weather", names)

    def test_get_parser_by_name(self) -> None:
        ossd_cls = get_parser_by_name("ossd")
        weather_cls = get_parser_by_name("weather")
        
        self.assertIs(ossd_cls, OssdParser)
        self.assertIs(weather_cls, WeatherParser)
    
    def test_get_parser_by_data_type(self) -> None:
        serial_parser = get_parser_by_data_type("serial")
        hid_parser = get_parser_by_data_type("hid")
        
        self.assertIs(serial_parser, OssdParser)
        self.assertIs(hid_parser, WeatherParser)


class OssdParserTests(unittest.TestCase):
    def test_parse_valid_ossd(self) -> None:
        result = OssdParser.parse("G0O,G1O,G2O,G3O")
        self.assertEqual(result, (True, True, True, True))
    
    def test_parse_mixed_ossd(self) -> None:
        result = OssdParser.parse("G0O,G1E,G2O,G3E")
        self.assertEqual(result, (True, False, True, False))
    
    def test_parse_invalid_returns_none(self) -> None:
        self.assertIsNone(OssdParser.parse(""))
        self.assertIsNone(OssdParser.parse("invalid"))
        self.assertIsNone(OssdParser.parse("G0O,G1O"))
    
    def test_validate(self) -> None:
        self.assertTrue(OssdParser.validate("G0O,G1O,G2O,G3O"))
        self.assertFalse(OssdParser.validate(""))
        self.assertFalse(OssdParser.validate("invalid"))
    
    def test_channel_meta(self) -> None:
        self.assertEqual(OssdParser.channel_meta(0), (1, 1))
        self.assertEqual(OssdParser.channel_meta(1), (1, 2))
        self.assertEqual(OssdParser.channel_meta(2), (2, 1))
        self.assertEqual(OssdParser.channel_meta(3), (2, 2))
    
    def test_status_to_string(self) -> None:
        self.assertEqual(OssdParser.status_to_string(True), "O")
        self.assertEqual(OssdParser.status_to_string(False), "E")


class WeatherParserTests(unittest.TestCase):
    def test_validate(self) -> None:
        self.assertTrue(WeatherParser.validate(b"\x00" * 19))
        self.assertTrue(WeatherParser.validate(b"\x00" * 32))
        self.assertFalse(WeatherParser.validate(b"\x00" * 18))
        self.assertFalse(WeatherParser.validate(""))
        self.assertFalse(WeatherParser.validate(None))
    
    def test_parse_valid_weather(self) -> None:
        raw = bytes([
            0, 0, 0, 0,
            50,
            0xF4, 0x01,
            0xF0, 0x02,
            0x18, 0x00,
            0, 4, 0, 0, 0,
            0x10, 0x27, 0,
        ])
        
        result = WeatherParser.parse(raw)
        self.assertIsNotNone(result)
        if result:
            self.assertEqual(result["humidity"], 50.0)
            self.assertEqual(result["temp"], 50.0)
            self.assertEqual(result["pressure"], 75.2)
            self.assertAlmostEqual(result["winds"], 1.2)
            self.assertEqual(result["winddir"], "E")
    
    def test_get_pointer_bytes(self) -> None:
        raw = bytes([0x12, 0x34])
        
        p_lo, p_hi = WeatherParser.get_pointer_bytes(raw, swap=False)
        self.assertEqual((p_lo, p_hi), (0x12, 0x34))
        
        p_lo, p_hi = WeatherParser.get_pointer_bytes(raw, swap=True)
        self.assertEqual((p_lo, p_hi), (0x34, 0x12))

    def test_sanity_issues_reports_bad_fields(self) -> None:
        issues = WeatherParser.sanity_issues(
            {
                "temp": 21.0,
                "pressure": 75.2,
                "humidity": 45.0,
                "winds": 2.1,
                "winddir": "NE",
                "rain": 0.0,
                "light": 500.0,
            }
        )

        self.assertIn("pressure=75.2", issues)
        self.assertFalse(WeatherParser.is_sane_payload(
            {
                "temp": 21.0,
                "pressure": 75.2,
                "humidity": 45.0,
                "winds": 2.1,
                "winddir": "NE",
                "rain": 0.0,
                "light": 500.0,
            }
        ))


if __name__ == "__main__":
    unittest.main()
