from __future__ import annotations


def normalize_ossd_status(value: object) -> str | None:
    text = str(value or "").strip().upper()
    if text in {"O", "E"}:
        return text

    return None
