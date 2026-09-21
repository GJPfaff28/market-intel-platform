"""Broader-market scan filters (PLANNING.md 'Broader market scan filters — DECIDED').

These apply ONLY to the broader-market-scan universe, not to the user's major
watchlist -- watchlist stocks are always evaluated regardless of price/volume/RVOL.
"""

from __future__ import annotations

from app.config import Settings
from app.data_providers.base import Quote


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
