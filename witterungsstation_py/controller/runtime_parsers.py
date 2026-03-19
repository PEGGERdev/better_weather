from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if isinstance(value, dict) and "$date" in value:
        value = value.get("$date")
    if isinstance(value, str):
        text = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed
        except Exception:
            pass
    return datetime.now(UTC)


def parse_oid(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and "$oid" in value:
        oid = value.get("$oid")
        return str(oid) if oid is not None else ""
    return ""
