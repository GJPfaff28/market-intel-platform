"""Builds the Market Overview tab's daily snapshot (PLANNING.md Tab 4): index
proxies, economic calendar, and earnings calendar (today + week ahead).
"""

from __future__ import annotations

import datetime as dt
import json
import logging

import httpx
from sqlalchemy.orm import Session

from app.data_providers.alpaca import AlpacaProvider
from app.data_providers.finnhub import FinnhubProvider
from app.db.models import MarketOverviewSnapshot

logger = logging.getLogger("scanner.market_overview")

# Real indices (S&P 500, Nasdaq, Dow, Russell 2000) aren't tradable equities on
# Alpaca's feed -- their liquid ETF proxies are used instead, same convention most
# retail tools use pre-market.
INDEX_PROXIES = {"S&P 500": "SPY", "Nasdaq": "QQQ", "Dow": "DIA", "Russell 2000": "IWM"}


def build_market_overview_snapshot(
    db: Session,
    market_data: AlpacaProvider,
    fundamentals: FinnhubProvider | None,
    today: dt.date,
) -> None:
    indices = {}
    quotes = market_data.get_snapshots(list(INDEX_PROXIES.values()))
    for label, proxy_ticker in INDEX_PROXIES.items():
        quote = quotes.get(proxy_ticker)
        if quote:
            indices[label] = {
                "proxy_ticker": proxy_ticker,
                "price": quote.price,
                "pct_change": round(quote.pct_change, 2),
            }

    earnings_calendar = []
    econ_calendar = []
    if fundamentals is not None:
        try:
            events = fundamentals.get_earnings_calendar(today, today + dt.timedelta(days=7))
            earnings_calendar = [
                {"ticker": e.ticker, "date": e.date.isoformat(), "when": e.when, "eps_estimate": e.eps_estimate}
                for e in events
            ]
        except httpx.HTTPStatusError:
            logger.warning("Earnings calendar fetch failed (check Finnhub plan/rate limits)")

        try:
            econ_calendar = _fetch_economic_calendar(fundamentals, today, today + dt.timedelta(days=7))
        except httpx.HTTPStatusError:
            # Finnhub's general economic calendar (FOMC/CPI/NFP) is gated on some
            # plan tiers; fail soft rather than breaking the whole scan.
            logger.warning("Economic calendar fetch failed -- may require a higher Finnhub tier")

    snapshot = MarketOverviewSnapshot(
        scan_date=today,
        indices_json=json.dumps(indices),
        econ_calendar_json=json.dumps(econ_calendar),
        earnings_calendar_json=json.dumps(earnings_calendar),
    )
    db.merge(snapshot)


def _fetch_economic_calendar(fundamentals: FinnhubProvider, start: dt.date, end: dt.date) -> list[dict]:
    events = fundamentals.get_economic_calendar_raw(start, end)
    return [
        {
            "event": e.get("event"),
            "country": e.get("country"),
            "date": e.get("time", "")[:10] if e.get("time") else None,
            "impact": e.get("impact"),
        }
        for e in events
    ]
