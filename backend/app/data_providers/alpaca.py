from __future__ import annotations

import datetime as dt

import httpx

from app.config import Settings
from app.data_providers.base import DailyBar, MarketDataProvider, NewsItem, NewsProvider, Quote

DATA_BASE_URL = "https://data.alpaca.markets"


class AlpacaProvider(MarketDataProvider, NewsProvider):
    """Free-tier Alpaca: real-time IEX quotes + Benzinga-powered news, $0/mo.
    See PLANNING.md "Data source recommendation" for why this was chosen.
    """

    def __init__(self, settings: Settings):
        self.feed = settings.alpaca_data_feed
        self._client = httpx.Client(
            base_url=DATA_BASE_URL,
            headers={
                "APCA-API-KEY-ID": settings.alpaca_api_key,
                "APCA-API-SECRET-KEY": settings.alpaca_secret_key,
            },
            timeout=10.0,
        )

    def close(self) -> None:
        self._client.close()

    def get_quote(self, ticker: str) -> Quote | None:
        snapshots = self.get_snapshots([ticker])
        return snapshots.get(ticker)

    def get_snapshots(self, tickers: list[str]) -> dict[str, Quote]:
        """Bulk snapshot fetch — the efficient path for scanning many tickers at once."""
        if not tickers:
            return {}
        result: dict[str, Quote] = {}
        # Alpaca caps symbols per request; chunk defensively.
        for i in range(0, len(tickers), 200):
            chunk = tickers[i : i + 200]
            resp = self._client.get(
                "/v2/stocks/snapshots",
                params={"symbols": ",".join(chunk), "feed": self.feed},
            )
            resp.raise_for_status()
            data = resp.json().get("snapshots", {})
            for symbol, snap in data.items():
                quote = self._snapshot_to_quote(symbol, snap)
                if quote:
                    result[symbol] = quote
        return result

    @staticmethod
    def _snapshot_to_quote(symbol: str, snap: dict) -> Quote | None:
        daily_bar = snap.get("dailyBar")
        prev_bar = snap.get("prevDailyBar")
        latest_trade = snap.get("latestTrade")
        if not daily_bar or not prev_bar:
            return None
        price = (latest_trade or {}).get("p") or daily_bar.get("c")
        if price is None:
            return None
        return Quote(
            ticker=symbol,
            price=price,
            prev_close=prev_bar.get("c", price),
            day_volume=daily_bar.get("v", 0),
            day_high=daily_bar.get("h", price),
            day_low=daily_bar.get("l", price),
        )

    def get_daily_bars(self, ticker: str, lookback_days: int) -> list[DailyBar]:
        end = dt.date.today()
        start = end - dt.timedelta(days=int(lookback_days * 1.6) + 5)  # pad for weekends/holidays
        resp = self._client.get(
            f"/v2/stocks/{ticker}/bars",
            params={
                "timeframe": "1Day",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "feed": self.feed,
                "limit": 1000,
                "adjustment": "split",
            },
        )
        resp.raise_for_status()
        bars = resp.json().get("bars", [])
        return [
            DailyBar(
                date=dt.datetime.fromisoformat(b["t"].replace("Z", "+00:00")).date(),
                open=b["o"],
                high=b["h"],
                low=b["l"],
                close=b["c"],
                volume=b["v"],
            )
            for b in bars
        ][-lookback_days:]

    def get_news(self, ticker: str, lookback_hours: int = 24) -> list[NewsItem]:
        return self._fetch_news(ticker=ticker, lookback_hours=lookback_hours)

    def get_market_news(self, lookback_hours: int = 18, limit: int = 50) -> list[NewsItem]:
        """General market news (no symbol filter) -- the macro/policy headline pool
        the Market Overview tab's sector driver attribution matches against
        (PLANNING.md Tab 4 sector breakdown, 'macro_policy' driver type)."""
        return self._fetch_news(ticker=None, lookback_hours=lookback_hours, limit=limit)

    def _fetch_news(self, ticker: str | None, lookback_hours: int, limit: int = 20) -> list[NewsItem]:
        since = dt.datetime.utcnow() - dt.timedelta(hours=lookback_hours)
        params = {"start": since.isoformat() + "Z", "limit": limit}
        if ticker:
            params["symbols"] = ticker
        resp = self._client.get("/v1beta1/news", params=params)
        resp.raise_for_status()
        items = resp.json().get("news", [])
        return [
            NewsItem(
                ticker=ticker or ",".join(item.get("symbols", [])),
                headline=item.get("headline", ""),
                summary=item.get("summary", ""),
                source=item.get("source", "Benzinga via Alpaca"),
                published_at=dt.datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                url=item.get("url", ""),
            )
            for item in items
        ]
