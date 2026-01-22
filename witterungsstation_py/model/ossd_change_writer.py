# model/ossd_change_writer.py
from __future__ import annotations

"""
Witterungstester – OSSDChangeWriter (Backend Sync Helper)

Role
- Reconstructs last-known OSSD state from backend history and can post changes "changed-only".

NOTE
- In the current controller, this is mainly used for initial sync (best-effort).
"""

from typing import List, Tuple, Optional, Callable
from datetime import datetime

from model.dto import OSSDEntryDTO, OSSDWriteResult
from model.db_client import DbClient

from exception_handler import format_current_exception


class OSSDChangeWriter:
    """
    Keeps the last persisted DB state and writes only on change.
    last_sent: List[Optional[bool]] for 4 channels.
    """

    def __init__(self, db: DbClient, logger: Callable[[str], None] | None = None) -> None:
        self._db = db
        self._log = logger or (lambda *_: None)
        self.last_sent: List[Optional[bool]] = [None, None, None, None]

    # ---------------- sync ----------------
    def sync_from_backend(self) -> List[Optional[bool]]:
        """
        Best-effort: fetches recent entries and reconstructs the last state per channel.

        NOTE
        - Router may return unsorted -> we sort best-effort by "time" (ISO string).
        """
        try:
            data = self._db.get_ossd_recent(limit=400)

            def _ts(x):
                t = x.get("time")
                return t if isinstance(t, str) else ""

            data = sorted(data, key=_ts)

            for x in data:
                lg = int(x.get("lichtgitterNr", 0))
                on = int(x.get("ossdNr", 0))
                st = str(x.get("ossdStatus", "E")) == "O"
                idx = (lg - 1) * 2 + (on - 1)   # (LG1 OSSD1 -> 0) etc.
                if idx in (0, 1, 2, 3):
                    self.last_sent[idx] = st
        except Exception as e:
            self._log(format_current_exception(f"GET /ossd failed: {e}"))
        return self.last_sent

    # ---------------- changed-only persist ----------------
    def persist_if_changed(self, state: Tuple[bool, bool, bool, bool], ts: datetime) -> OSSDWriteResult:
        posted = 0
        skipped = 0
        for idx, val in enumerate(state):
            if self.last_sent[idx] is None or self.last_sent[idx] != val:
                lg = 1 if idx < 2 else 2
                on = 1 if idx % 2 == 0 else 2
                entry = OSSDEntryDTO(time=ts, lichtgitterNr=lg, ossdNr=on, ossdStatus=("O" if val else "E"))
                try:
                    self._db.post_ossd(entry)
                    self.last_sent[idx] = val
                    posted += 1
                except Exception as e:
                    self._log(format_current_exception(f"POST /ossd failed: {e}"))
            else:
                skipped += 1
        return OSSDWriteResult(posted=posted, skipped=skipped)
