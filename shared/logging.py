from __future__ import annotations

"""
Shared logging service.

Provides centralized logging with configurable level.
"""

import logging
import sys
from typing import Callable, Optional


def create_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def create_log_function(name: str, level: str = "INFO") -> Callable[[str], None]:
    logger = create_logger(name, level)
    return lambda msg: logger.info(msg)


class LogGateway:
    def __init__(self, name: str = "app", level: str = "INFO") -> None:
        self._logger = create_logger(name, level)
        self._callback: Optional[Callable[[str], None]] = None

    def set_callback(self, callback: Optional[Callable[[str], None]]) -> None:
        self._callback = callback

    def __call__(self, message: str) -> None:
        self._logger.info(message)
        if self._callback:
            try:
                self._callback(message)
            except Exception:
                pass

    def debug(self, message: str) -> None:
        self._logger.debug(message)
        if self._callback:
            try:
                self._callback(f"[DEBUG] {message}")
            except Exception:
                pass

    def info(self, message: str) -> None:
        self._logger.info(message)
        if self._callback:
            try:
                self._callback(message)
            except Exception:
                pass

    def warning(self, message: str) -> None:
        self._logger.warning(message)
        if self._callback:
            try:
                self._callback(f"[WARN] {message}")
            except Exception:
                pass

    def error(self, message: str) -> None:
        self._logger.error(message)
        if self._callback:
            try:
                self._callback(f"[ERROR] {message}")
            except Exception:
                pass
