from __future__ import annotations


class BaseService:
    def __init__(self, service_name: str = "service") -> None:
        self.service_name = str(service_name or "service")
        self._last_error = ""

    def last_error(self) -> str:
        return self._last_error

    def clear_error(self) -> None:
        self._last_error = ""

    def capture_error(self, error: object, fallback_message: str = "") -> None:
        fallback = fallback_message or f"Unknown {self.service_name} error"
        text = str(error).strip()
        self._last_error = text or fallback
