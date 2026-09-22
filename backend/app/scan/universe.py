"""The broader-market scan universe.

Two layers:
  - data/universe.csv -- a curated ~120-ticker seed list with GICS sector mapping,
    always loaded. Used for both broader-scan discovery and the Market Overview tab's
    sector breakdown (which needs a `sector` per ticker).
  - data/universe_full.csv -- an optional, much larger ticker-only list (thousands of
    names) covering the real full market, produced by running
    `python -m app.scan.refresh_universe` (see that file's docstring -- it needs real
    internet access NASDAQ's public symbol directory, so it's not run automatically).
    If present, its tickers are merged in for scan coverage; they just won't have a
    sector (sector_for_ticker().get(ticker) returns None for them, which the
    orchestrator already treats as "no sector attribution" for that name).

If universe_full.csv doesn't exist, load_universe() falls back to the curated list
alone, so the scanner still works out of the box without extra setup. See README.md
"Growing the scan universe".
"""

from __future__ import annotations

import csv
from pathlib import Path

UNIVERSE_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "universe.csv"
FULL_UNIVERSE_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "universe_full.csv"


def _read_csv(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open(newline="") as f:
        return list(csv.DictReader(f))


def load_universe(
    csv_path: Path = UNIVERSE_CSV_PATH, full_csv_path: Path = FULL_UNIVERSE_CSV_PATH
) -> list[dict[str, str]]:
    curated_rows = _read_csv(csv_path)
    known_tickers = {row["ticker"] for row in curated_rows}

    full_rows = _read_csv(full_csv_path)
    extra_rows = [{"ticker": row["ticker"], "sector": ""} for row in full_rows if row["ticker"] not in known_tickers]

    return curated_rows + extra_rows


def load_universe_tickers(csv_path: Path = UNIVERSE_CSV_PATH) -> list[str]:
    return [row["ticker"] for row in load_universe(csv_path)]


def sector_for_ticker(csv_path: Path = UNIVERSE_CSV_PATH) -> dict[str, str]:
    return {row["ticker"]: row["sector"] for row in load_universe(csv_path) if row["sector"]}
