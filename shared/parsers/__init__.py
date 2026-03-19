from __future__ import annotations

from shared.parser_registry import (
    BaseParser,
    ParserBinding,
    register_parser,
    get_parsers,
    get_parser_by_name,
    get_parser_by_data_type,
)
from shared.parsers.ossd_parser import OssdParser
from shared.parsers.weather_parser import WeatherParser

__all__ = [
    "BaseParser",
    "ParserBinding",
    "register_parser",
    "get_parsers",
    "get_parser_by_name",
    "get_parser_by_data_type",
    "OssdParser",
    "WeatherParser",
]
