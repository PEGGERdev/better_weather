from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonlQueue:
    """Small file-backed FIFO queue for JSON-serializable dict items."""

    def __init__(self, path: str | Path, *, on_error=None) -> None:
        self._path = Path(path)
        self._on_error = on_error or (lambda _msg: None)

    def load(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []

        out: list[dict[str, Any]] = []
        try:
            with self._path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    text = line.strip()
                    if not text:
                        continue
                    item = json.loads(text)
                    if isinstance(item, dict):
                        out.append(item)
        except Exception:
            self._on_error(f"Failed to read queue: {self._path}")
        return out

    def save(self, items: list[dict[str, Any]]) -> None:
        try:
            if not items:
                if self._path.exists():
                    self._path.unlink()
                return
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("w", encoding="utf-8") as handle:
                for item in items:
                    handle.write(json.dumps(item, ensure_ascii=True) + "\n")
        except Exception:
            self._on_error(f"Failed to write queue: {self._path}")

    def append(self, item: dict[str, Any]) -> None:
        items = self.load()
        items.append(item)
        self.save(items)
