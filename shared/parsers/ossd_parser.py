from __future__ import annotations

"""
OSSD Parser.

Parses serial data from Arduino OSSD hardware.
Format: "G0O,G1O,G2O,G3O" where O=OK (True), E=Error (False)
"""

import re
from typing import Optional, Tuple

from shared.parser_registry import BaseParser, register_parser


@register_parser(
    name="ossd",
    data_type="serial",
    description="Parses OSSD state from Arduino serial output",
)
class OssdParser(BaseParser):
    """Parses OSSD channel states from serial data."""
    
    _PATTERN = re.compile(r"G([0-3])([OE])")
    
    @classmethod
    def parse(cls, raw: str) -> Optional[Tuple[bool, bool, bool, bool]]:
        """
        Parse OSSD state string into tuple of 4 booleans.
        
        Args:
            raw: Raw string like "G0O,G1O,G2O,G3O"
            
        Returns:
            Tuple of 4 booleans (True=OK, False=Error) or None if invalid
        """
        if not raw:
            return None
        
        matches = cls._PATTERN.findall(raw)
        if len(matches) != 4:
            return None
        
        vals = [None, None, None, None]
        for idx, ch in matches:
            vals[int(idx)] = (ch == "O")
        
        if any(v is None for v in vals):
            return None
        
        return (bool(vals[0]), bool(vals[1]), bool(vals[2]), bool(vals[3]))
    
    @classmethod
    def validate(cls, data: str) -> bool:
        """Check if data looks like valid OSSD output."""
        if not data or not isinstance(data, str):
            return False
        return bool(cls._PATTERN.search(data))
    
    @classmethod
    def channel_meta(cls, idx: int) -> Tuple[int, int]:
        """Map channel index to (lichtgitterNr, ossdNr)."""
        lg = 1 if idx < 2 else 2
        on = 1 if idx % 2 == 0 else 2
        return lg, on
    
    @classmethod
    def status_to_string(cls, is_ok: bool) -> str:
        """Convert boolean status to string."""
        return "O" if is_ok else "E"
