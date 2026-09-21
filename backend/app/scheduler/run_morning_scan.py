"""Entry point for the scheduled pre-market scan.

Run manually with:  python -m app.scheduler.run_morning_scan
Windows Task Scheduler wires this up to fire at 8:00 AM ET daily (PLANNING.md
'Run mode' -- see README.md "Scheduling the morning scan" for the exact setup steps).
"""

from __future__ import annotations

import logging
import sys

from app.db.base import SessionLocal, init_db
from app.scan.orchestrator import run_morning_scan

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("scanner.scheduler")


def main() -> int:
    init_db()
    db = SessionLocal()
    try:
        result = run_morning_scan(db)
    finally:
        db.close()

    logger.info("Morning scan result: %s", result)
    if result.get("status") != "ok":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
