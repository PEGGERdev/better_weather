from __future__ import annotations

import threading
import time
from typing import Callable, Optional


class RuntimeLoop:
    def __init__(self, poll_sec: float, step: Callable[[], None]) -> None:
        self._poll = max(0.2, float(poll_sec))
        self._step = step
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        if self.is_running():
            return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="live-runtime")
        self._thread.start()
        return True

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def run_once(self) -> None:
        self._step()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._step()
            time.sleep(self._poll)
