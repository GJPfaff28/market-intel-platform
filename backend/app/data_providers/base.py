"""Provider-agnostic data types. Alpaca/Finnhub clients (or a future Massive/Polygon
client) all normalize into these, so the scan/setup/catalyst logic never touches a
vendor-specific response shape directly.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass
class DailyBar:
    date: dt.date
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class Quote:
    ticker: str
    price: float
    prev_close: float
    day_volume: int
    day_high: float
    day_low: float

    @property
    def pct_change(self) -> float:
        if not self.prev_close:
            return 0.0
        return (self.price - self.prev_close) / self.prev_close * 100


@dataclass
class NewsItem:
    ticker: str
    headline: str
    summary: str
    source: str
    published_at: dt.datetime
    url: str = ""
    # How many tickers the source article was tagged with. Alpaca's news search
    # returns broad "10 stocks whale activity" / market-wrap roundups tagged with
    # every ticker they mention in passing, alongside genuine single-stock catalyst
    # articles -- this lets callers prefer the latter. See catalysts/scoring.py.
    tagged_symbol_count: int = 1
    # True for items from a source that's inherently per-company (e.g. Finnhub's
    # /company-news, a dedicated feed per ticker), as opposed to Alpaca's broader
    # symbol-tagged search. Skips the headline-text relevance check in
    # catalysts/scoring.py, since a company name in the text ("Google" vs ticker
    # "GOOGL") won't always literally match the ticker string even when the
    # article genuinely is about that company.
    verified_relevant: bool = False


@dataclass
class EarningsEvent:
    ticker: str
    date: dt.date
    when: str  # "bmo" (before market open), "amc" (after market close), "unknown"
    eps_estimate: float | None = None


@dataclass
class AnalystAction:
    ticker: str
    firm: str
    action: str  # "upgrade", "downgrade", "initiate", "price_target"
    from_grade: str | None
    to_grade: str | None
    published_at: dt.datetime


class MarketDataProvider:
    """Interface every market-data provider implements. Not an ABC on purpose —
    duck typing is enough for a single-user local tool, and it keeps swapping in a
    new provider (e.g. Massive/Polygon) a matter of implementing these methods.
    """

    def get_quote(self, ticker: str) -> Quote | None:
        raise NotImplementedError

    def get_daily_bars(self, ticker: str, lookback_days: int) -> list[DailyBar]:
        raise NotImplementedError

    def get_avg_volume(self, ticker: str, lookback_days: int = 20) -> float:
        bars = self.get_daily_bars(ticker, lookback_days)
        if not bars:
            return 0.0
        return sum(b.volume for b in bars) / len(bars)


class NewsProvider:
    def get_news(self, ticker: str, lookback_hours: int = 24) -> list[NewsItem]:
        raise NotImplementedError


class FundamentalsProvider:
    def get_earnings_calendar(self, start: dt.date, end: dt.date) -> list[EarningsEvent]:
        raise NotImplementedError

    def get_analyst_actions(self, ticker: str, lookback_days: int = 3) -> list[AnalystAction]:
        raise NotImplementedError

    def get_market_cap(self, ticker: str) -> float | None:
        raise NotImplementedError

    def get_float_shares(self, ticker: str) -> float | None:
        raise NotImplementedError
