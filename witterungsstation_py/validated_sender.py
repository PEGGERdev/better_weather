from __future__ import annotations

"""Deprecated entrypoint kept for backward compatibility.

Canonical ingestion runtime is now `data_handler_service.py`.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data_handler_service import main as data_handler_main


def main() -> None:
    data_handler_main()


if __name__ == "__main__":
    main()
