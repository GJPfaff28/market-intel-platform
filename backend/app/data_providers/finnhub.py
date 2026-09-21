from __future__ import annotations

import datetime as dt
import logging
import time

import httpx

from app.config import Settings
from app.data_providers.base import AnalystAction, EarningsEvent, FundamentalsProvider

BASE_URL = "https://finnhub.io/api/v1"

_HOUR_MAP = {"bmo": "bmo", "amc": "amc", "dmh": "unknown"}

logger = logging.getLogger("scanner.finnhub")

# Finnhub's free tier caps out around 60 requests/minute. A scan touches this
# endpoint once per evaluated ticker (100+ per run), so without throttling it
# reliably hits 429s partway through -- which used to crash the whole scan.
# Staying under ~55/min leaves headroom for other Finnhub calls in the same run.
_MIN_REQUEST_INTERVAL_SECONDS = 60 / 55


class FinnhubProvider(FundamentalsProvider):
    """Free-tier Finnhub: earnings calendar, analyst actions, company fundamentals.
    Used for catalyst detection (earnings, analyst upgrades/downgrades) and for the
    large-cap/small-cap market-cap split used by the Day 2/3 setup's Day-1 threshold.
    """

    def __init__(self, settings: Settings):
        self._token = settings.finnhub_api_key
        self._client = httpx.Client(base_url=BASE_URL, timeout=10.0)
        self._last_request_at = 0.0

    def close(self) -> None:
        self._client.close()

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        wait = _MIN_REQUEST_INTERVAL_SECONDS - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.monotonic()

    def _get(self, path: str, params: dict, retry_on_429: bool = True) -> dict | list | None:
        """Fails soft: logs and returns None on any error instead of raising, so
        one ticker's rate limit or plan-tier gate doesn't take down the whole scan.
        Retries once on 429 after a short backoff, since that's usually transient.
        """
        self._throttle()
        params = {**params, "token": self._token}
        try:
            resp = self._client.get(path, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429 and retry_on_429:
                logger.warning("Finnhub 429 on %s -- backing off 5s and retrying once", path)
                time.sleep(5)
                return self._get(path, {k: v for k, v in params.items() if k != "token"}, retry_on_429=False)
            logger.warning("Finnhub request failed (%s): %s", path, exc)
            return None
        except httpx.RequestError as exc:
            logger.warning("Finnhub request failed (%s): %s", path, exc)
            return None

    def get_economic_calendar_raw(self, start: dt.date, end: dt.date) -> list[dict]:
        """Scheduled macro events (FOMC, CPI, NFP, etc.). Gated on some Finnhub plan
        tiers -- callers should expect this to raise httpx.HTTPStatusError and fail
        soft if the account doesn't have access."""
        data = self._get("/calendar/economic", {"from": start.isoformat(), "to": end.isoformat()})
        return data.get("economicCalendar", []) if isinstance(data, dict) else []

    def get_earnings_calendar(self, start: dt.date, end: dt.date) -> list[EarningsEvent]:
        data = self._get(
            "/calendar/earnings",
            {"from": start.isoformat(), "to": end.isoformat()},
        )
        events = data.get("earningsCalendar", []) if isinstance(data, dict) else []
        return [
            EarningsEvent(
                ticker=e["symbol"],
                date=dt.date.fromisoformat(e["date"]),
                when=_HOUR_MAP.get(e.get("hour", ""), "unknown"),
                eps_estimate=e.get("epsEstimate"),
            )
            for e in events
        ]

    def get_analyst_actions(self, ticker: str, lookback_days: int = 3) -> list[AnalystAction]:
        # Finnhub's upgrade/downgrade endpoint is gated on some plans; _get() fails
        # soft (returns None) rather than raising, so this just falls through to [].
        since = dt.date.today() - dt.timedelta(days=lookback_days)
        data = self._get(
            "/stock/upgrade-downgrade",
            {"symbol": ticker, "from": since.isoformat(), "to": dt.date.today().isoformat()},
        )
        rows = data if isinstance(data, list) else []
        return [
            AnalystAction(
                ticker=ticker,
                firm=row.get("company", "Unknown"),
                action=row.get("action", "unknown"),
                from_grade=row.get("fromGrade") or None,
                to_grade=row.get("toGrade") or None,
                published_at=dt.datetime.fromtimestamp(row.get("gradeTime", 0), tz=dt.timezone.utc),
            )
            for row in rows
        ]

    def get_company_profile(self, ticker: str) -> tuple[float | None, float | None]:
        """Returns (market_cap, float_shares_approx) in ONE API call.

        Finnhub's free profile2 doesn't expose true free-float; shares outstanding
        is used as the closest available approximation (documented in PLANNING.md's
        data-source notes as an accepted MVP tradeoff).
        """
        profile = self._get("/stock/profile2", {"symbol": ticker})
        if not isinstance(profile, dict):
            return None, None
        cap_millions = profile.get("marketCapitalization")
        shares_millions = profile.get("shareOutstanding")
        market_cap = cap_millions * 1_000_000 if cap_millions else None
        float_shares = shares_millions * 1_000_000 if shares_millions else None
        return market_cap, float_shares

    def get_market_cap(self, ticker: str) -> float | None:
        market_cap, _ = self.get_company_profile(ticker)
        return market_cap

    def get_float_shares(self, ticker: str) -> float | None:
        _, float_shares = self.get_company_profile(ticker)
        return float_shares
