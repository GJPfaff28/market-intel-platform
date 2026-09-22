"""Broader-market scan filters (PLANNING.md 'Broader market scan filters — DECIDED').

These apply ONLY to the broader-market-scan universe, not to the user's major
watchlist -- watchlist stocks are always evaluated regardless of price/volume/RVOL.
"""

from __future__ import annotations

from app.config import Settings
from app.data_providers.base import DailyBar, Quote
from app.setups.day2_3 import LARGE_CAP_THRESHOLD_USD
from app.setups.indicators import atr as compute_atr

# Quality gate applied to EVERY setup match regardless of source (watchlist or
# broader scan) -- user-specified requirement: "these setups should have 2 RVOL,
# 1 ATR, over 3% change in pre market for mega caps and for small caps 6%". Unlike
# passes_broader_scan_filters below (discovery-only, broader-scan side), this is a
# defining characteristic of a valid setup, so it applies to watchlist names too.
SETUP_MIN_RVOL = 2.0
SETUP_MIN_ATR_MULTIPLE = 1.0
MEGA_CAP_MIN_PCT_CHANGE = 0.03
SMALL_CAP_MIN_PCT_CHANGE = 0.06


def rvol(quote: Quote, avg_volume: float) -> float:
    if not avg_volume:
        return 0.0
    return quote.day_volume / avg_volume


def passes_broader_scan_filters(quote: Quote, avg_volume: float, settings: Settings) -> bool:
    if quote.price < settings.scan_min_price:
        return False
    if avg_volume < settings.scan_min_avg_volume:
        return False
    if rvol(quote, avg_volume) < settings.scan_min_rvol:
        return False
    return True


def passes_setup_quality_gate(
    quote: Quote, avg_volume: float, bars: list[DailyBar], market_cap: float | None
) -> bool:
    """A setup match only counts if RVOL >= 2, today's move is at least 1x ATR, and
    the pre-market % change clears 3% (mega/large cap, >= $2B) or 6% (small cap)."""
    if rvol(quote, avg_volume) < SETUP_MIN_RVOL:
        return False

    today_move = abs(quote.price - quote.prev_close)
    atr_value = compute_atr(bars)
    if atr_value <= 0 or today_move < SETUP_MIN_ATR_MULTIPLE * atr_value:
        return False

    pct_threshold = MEGA_CAP_MIN_PCT_CHANGE if (market_cap or 0) >= LARGE_CAP_THRESHOLD_USD else SMALL_CAP_MIN_PCT_CHANGE
    if abs(quote.pct_change) / 100 < pct_threshold:
        return False

    return True
