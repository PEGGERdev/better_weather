#!/usr/bin/env python3
from __future__ import annotations

import sys


def main() -> int:
    from data_handler.core import DataHandler

    handler = DataHandler()
    try:
        handler.run()
    except KeyboardInterrupt:
        handler.stop()
    finally:
        handler.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
