"""The broader-market scan universe.

MVP ships with a static seed list (data/universe.csv, ~120 liquid names across all 11
GICS sectors) rather than a live full-exchange listing, to keep the scanner runnable
without extra setup. Refresh it any time by replacing that CSV with a fuller list --
e.g. NASDAQ's free public symbol directory
(ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt and otherlisted.txt) --
keeping the same `ticker,sector` columns. See README.md "Growing the scan universe".
"""

from __future__ import annotations

import csv
from pathlib import Path

UNIVERSE_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "universe.csv"


def load_universe(csv_path: Path = UNIVERSE_CSV_PATH) -> list[dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open(newline="") as f:
        return list(csv.DictReader(f))


def load_universe_tickers(csv_path: Path = UNIVERSE_CSV_PATH) -> list[str]:
    return [row["ticker"] for row in load_universe(csv_path)]


def sector_for_ticker(csv_path: Path = UNIVERSE_CSV_PATH) -> dict[str, str]:
    return {row["ticker"]: row["sector"] for row in load_universe(csv_path)}
