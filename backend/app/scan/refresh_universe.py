"""One-off/occasional script to refresh the broader-scan universe with NASDAQ's real,
free full US-listed symbol directory (thousands of tickers) instead of the ~120-ticker
starter list in data/universe.csv.

This is NOT part of the daily scheduled scan -- it needs real internet access to NASDAQ's
public FTP-over-HTTP mirror, which this sandbox doesn't have. Run it yourself, occasionally
(tickers get added/delisted over time):

    cd backend
    venv\\Scripts\\activate      (Windows)  /  source venv/bin/activate   (Mac/Linux)
    python -m app.scan.refresh_universe

It writes backend/data/universe_full.csv (ticker-only -- these files don't carry sector
data, and per-ticker sector lookups for thousands of names isn't practical under Finnhub's
free-tier rate limit). load_universe() in universe.py merges this with the existing
sector-mapped universe.csv (kept as-is for the Market Overview tab's sector breakdown) to
scan the full list while still having sector data for the ~120 starter names.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import httpx

NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"

FULL_UNIVERSE_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "universe_full.csv"

# Plain common-stock tickers only -- 1-5 uppercase letters. Excludes preferred shares,
# warrants, units, and other suffixed share classes (e.g. "BRK.A", "ABC.W", "ABC.U"),
# which the setups/catalyst logic isn't designed to evaluate.
_TICKER_RE = re.compile(r"^[A-Z]{1,5}$")


def _parse_pipe_delimited(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line and not line.startswith("File Creation Time")]
    reader = csv.DictReader(lines, delimiter="|")
    return list(reader)


def fetch_nasdaq_listed() -> list[str]:
    resp = httpx.get(NASDAQ_LISTED_URL, timeout=30.0)
    resp.raise_for_status()
    rows = _parse_pipe_delimited(resp.text)
    return [
        row["Symbol"]
        for row in rows
        if row.get("Test Issue") == "N" and row.get("ETF") == "N" and _TICKER_RE.match(row.get("Symbol", ""))
    ]


def fetch_other_listed() -> list[str]:
    resp = httpx.get(OTHER_LISTED_URL, timeout=30.0)
    resp.raise_for_status()
    rows = _parse_pipe_delimited(resp.text)
    return [
        row["ACT Symbol"]
        for row in rows
        if row.get("Test Issue") == "N" and row.get("ETF") == "N" and _TICKER_RE.match(row.get("ACT Symbol", ""))
    ]


def refresh_universe() -> int:
    tickers = sorted(set(fetch_nasdaq_listed()) | set(fetch_other_listed()))

    FULL_UNIVERSE_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FULL_UNIVERSE_CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker"])
        for ticker in tickers:
            writer.writerow([ticker])

    return len(tickers)


if __name__ == "__main__":
    count = refresh_universe()
    print(f"Wrote {count} tickers to {FULL_UNIVERSE_CSV_PATH}")
