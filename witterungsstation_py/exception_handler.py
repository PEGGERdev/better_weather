# exception_handler.py
from __future__ import annotations

"""
Witterungstester – Exception/Traceback Utilities

Role
- Provides a consistent exception/traceback formatting + safe logging.
- Installs global hooks (sys + threading) to capture full tracebacks.

Error handling
- Logging must never raise further exceptions (safe_log).
"""

from typing import Callable, Optional
import datetime
import sys
import traceback

LogFn = Callable[[str], None]
PostFn = Callable[[Callable[[], None]], None]


def _ts() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def format_current_exception(context: str) -> str:
    """
    Must be called inside an `except:` block.
    Returns context + stacktrace.
    """
    tb = traceback.format_exc().rstrip()
    return f"[{_ts()}] {context}\n{tb}"


def format_exception(context: str, exc_type, exc, tb) -> str:
    """
    For sys/thread excepthooks where exc_type/exc/tb are provided separately.
    """
    tb_txt = "".join(traceback.format_exception(exc_type, exc, tb)).rstrip()
    return f"[{_ts()}] {context}: {exc}\n{tb_txt}"


def safe_log(log: Optional[LogFn], text: str) -> None:
    """
    Logs to GUI console (if log is provided) or falls back to stderr.
    Must never raise exceptions outward.
    """
    if log is None:
        try:
            sys.stderr.write(text + ("\n" if not text.endswith("\n") else ""))
        except Exception:
            pass
        return

    try:
        log(text)
    except Exception:
        try:
            sys.stderr.write(text + ("\n" if not text.endswith("\n") else ""))
        except Exception:
            pass


def install_global_exception_hooks(
    log: Optional[LogFn],
    post: Optional[PostFn] = None,
) -> None:
    """
    Ensures unhandled exceptions (main + threads) are logged with a full traceback.
    post: if provided, logging is dispatched thread-safely to the GUI thread.
    """

    def emit(text: str) -> None:
        if post:
            try:
                post(lambda: safe_log(log, text))
                return
            except Exception:
                pass
        safe_log(log, text)

    def _sys_hook(exc_type, exc, tb) -> None:
        emit(format_exception("Uncaught exception", exc_type, exc, tb))

    sys.excepthook = _sys_hook

    # Threads (Py>=3.8)
    try:
        import threading
        if hasattr(threading, "excepthook"):
            def _thread_hook(args) -> None:
                emit(
                    format_exception(
                        f"Uncaught exception in thread '{args.thread.name}'",
                        args.exc_type,
                        args.exc_value,
                        args.exc_traceback,
                    )
                )
            threading.excepthook = _thread_hook
    except Exception:
        pass
