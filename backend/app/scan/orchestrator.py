"""The morning scan job (PLANNING.md 'Run mode' -- scheduled 8:00 AM ET run that
writes results to SQLite for the dashboard to read).

Evaluates the major watchlist (no filters) plus the broader-scan universe (gated by
price/avg-volume/RVOL filters), against all 3 setups and the catalyst engine, and
persists ScanCandidate/SetupMatch/CatalystTag/NearMiss/SectorOverview rows for today.
"""

from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy.orm import Session

from app.catalysts.scoring import build_catalyst_tags, float_context, pick_best_headline
from app.catalysts.sectors import GICS_SECTORS, attribute_sector_driver
from app.config import Settings, get_settings
from app.data_providers.base import DailyBar, NewsItem
from app.data_providers.factory import get_fundamentals_provider, get_market_data_provider
from app.db.models import (
    CandidateSource,
    CatalystTag,
    MarketOverviewSnapshot,
    NearMiss,
    ScanCandidate,
    SectorOverview,
    SetupMatch,
    WatchlistStock,
)
from app.scan.filters import passes_broader_scan_filters, passes_setup_quality_gate, rvol as compute_rvol
from app.scan.market_overview import build_market_overview_snapshot
from app.scan.universe import load_universe
from app.setups.engine import evaluate_near_misses, evaluate_setups

logger = logging.getLogger("scanner.orchestrator")

BAR_LOOKBACK_DAYS = 260  # enough for the 52-week-high check in Setup 1


def _avg_volume(bars: list[DailyBar], window: int = 20) -> float:
    if not bars:
        return 0.0
    recent = bars[-window:]
    return sum(b.volume for b in recent) / len(recent)


def _cached_combined_news(
    market_data, fundamentals, cache: dict[str, list[NewsItem]], ticker: str, lookback_hours: int, today: dt.date
) -> list[NewsItem]:
    """Per-run cache so a ticker that's both a scan candidate AND a sector's top
    mover only costs one round of news calls, not two. Combines Alpaca's broader
    symbol-search (noisier, but catches things Finnhub might not) with Finnhub's
    per-company feed (more reliable relevance -- see NewsItem.verified_relevant),
    letting catalysts/scoring.py's relevance sort pick the best of both.
    """
    if ticker not in cache:
        alpaca_news = market_data.get_news(ticker, lookback_hours=lookback_hours) if hasattr(market_data, "get_news") else []
        finnhub_news = (
            fundamentals.get_company_news(ticker, today - dt.timedelta(days=2), today) if fundamentals else []
        )
        cache[ticker] = alpaca_news + finnhub_news
    return cache[ticker]


def run_morning_scan(db: Session, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    today = dt.date.today()

    market_data = get_market_data_provider(settings)
    fundamentals = get_fundamentals_provider(settings)

    if market_data is None:
        logger.warning("No Alpaca API keys configured -- skipping scan (see README 'Getting API keys').")
        return {"status": "skipped", "reason": "market_data_provider_not_configured"}

    watchlist_tickers = [row.ticker for row in db.query(WatchlistStock).all()]
    universe_rows = load_universe()
    universe_tickers = [row["ticker"] for row in universe_rows]
    sector_by_ticker = {row["ticker"]: row["sector"] for row in universe_rows}

    ticker_sources: dict[str, CandidateSource] = {t: CandidateSource.WATCHLIST for t in watchlist_tickers}
    for t in universe_tickers:
        ticker_sources.setdefault(t, CandidateSource.BROADER_SCAN)

    all_tickers = list(ticker_sources.keys())
    quotes = market_data.get_snapshots(all_tickers)

    # Clear today's prior run (re-running the scan for the same day replaces results).
    # Deliberately NOT committed here -- it stays in the same transaction as the
    # rebuild below, with one commit at the very end. Live testing showed that
    # committing the delete early creates a real window (the ~2-3 minutes a scan
    # takes) where anyone loading the dashboard mid-scan sees today's data wiped
    # but not yet rebuilt. Keeping it all in one transaction means other readers
    # (SQLite doesn't block readers against an uncommitted writer) keep seeing
    # yesterday's complete data right up until this scan's results are all ready
    # and committed at once, instead of a misleading empty gap.
    db.query(ScanCandidate).filter(ScanCandidate.scan_date == today).delete()
    db.query(NearMiss).filter(NearMiss.scan_date == today).delete()
    db.query(SectorOverview).filter(SectorOverview.scan_date == today).delete()
    db.query(MarketOverviewSnapshot).filter(MarketOverviewSnapshot.scan_date == today).delete()

    candidates_written = 0
    near_misses_written = 0
    sector_moves: dict[str, list[tuple[str, float]]] = {s: [] for s in GICS_SECTORS}
    news_cache: dict[str, list[NewsItem]] = {}

    for ticker, source in ticker_sources.items():
        quote = quotes.get(ticker)
        if quote is None:
            continue

        sector = sector_by_ticker.get(ticker)
        if sector in sector_moves:
            sector_moves[sector].append((ticker, quote.pct_change))

        try:
            bars = market_data.get_daily_bars(ticker, BAR_LOOKBACK_DAYS)
        except Exception:  # noqa: BLE001 -- one bad ticker shouldn't kill the scan
            logger.exception("Failed to fetch bars for %s", ticker)
            continue

        avg_volume = _avg_volume(bars)

        if source == CandidateSource.BROADER_SCAN and not passes_broader_scan_filters(quote, avg_volume, settings):
            continue

        market_cap = fundamentals.get_market_cap(ticker) if fundamentals else None
        float_shares = fundamentals.get_float_shares(ticker) if fundamentals else None

        setup_matches = evaluate_setups(bars, market_cap)
        near_misses = evaluate_near_misses(bars, market_cap)

        # A raw pattern match isn't enough on its own -- user-specified quality gate
        # (RVOL >= 2, move >= 1 ATR, pre-market % over 3%/6% by cap size) applies to
        # every setup match regardless of source, since it's a defining property of
        # a valid setup, not just a broader-scan discovery filter.
        if setup_matches and not passes_setup_quality_gate(quote, avg_volume, bars, market_cap):
            setup_matches = []

        if setup_matches:
            candidate = ScanCandidate(
                scan_date=today,
                ticker=ticker,
                source=source,
                price=quote.price,
                pct_change=quote.pct_change,
                rvol=compute_rvol(quote, avg_volume),
                avg_volume=int(avg_volume),
                day_volume=quote.day_volume,
                market_cap=market_cap,
                float_shares=float_shares,
            )
            db.add(candidate)
            db.flush()  # get candidate.id

            for match in setup_matches:
                db.add(
                    SetupMatch(
                        candidate_id=candidate.id,
                        setup_type=match.setup_type,
                        timeframe=match.timeframe,
                        day_number=match.day_number,
                        detail=match.detail,
                    )
                )

            _attach_catalyst_tags(db, candidate, ticker, today, bars, market_data, fundamentals, float_shares, news_cache)
            candidates_written += 1

        for nm in near_misses:
            db.add(
                NearMiss(
                    scan_date=today,
                    ticker=ticker,
                    setup_type=nm.setup_type,
                    proximity_pct=nm.proximity_pct,
                    price=quote.price,
                    pct_change=quote.pct_change,
                    rvol=compute_rvol(quote, avg_volume),
                    detail=nm.detail,
                )
            )
            near_misses_written += 1

    _write_sector_overview(db, today, sector_moves, market_data, fundamentals, news_cache)
    build_market_overview_snapshot(db, market_data, fundamentals, today)

    db.commit()
    return {
        "status": "ok",
        "scan_date": today.isoformat(),
        "candidates": candidates_written,
        "near_misses": near_misses_written,
        "tickers_evaluated": len(all_tickers),
    }


def _attach_catalyst_tags(db, candidate, ticker, today, bars, market_data, fundamentals, float_shares, news_cache):
    news_items = _cached_combined_news(market_data, fundamentals, news_cache, ticker, lookback_hours=48, today=today)
    earnings_events = (
        fundamentals.get_earnings_calendar(today, today) if fundamentals else []
    )
    analyst_actions = fundamentals.get_analyst_actions(ticker) if fundamentals else []

    catalyst_results = build_catalyst_tags(
        today=today,
        bars=bars,
        news_items=news_items,
        earnings_events=[e for e in earnings_events if e.ticker == ticker],
        analyst_actions=analyst_actions,
    )
    float_note = float_context(float_shares)
    for tag in catalyst_results:
        db.add(
            CatalystTag(
                candidate_id=candidate.id,
                kind=tag.kind,
                category=tag.category,
                summary=f"{tag.summary} ({float_note})",
                priced_in_flag=tag.priced_in_flag,
            )
        )


def _write_sector_overview(
    db: Session,
    today: dt.date,
    sector_moves: dict[str, list[tuple[str, float]]],
    market_data,
    fundamentals,
    news_cache: dict[str, list[NewsItem]],
) -> None:
    macro_headlines: list[str] = []
    if hasattr(market_data, "get_market_news"):
        try:
            macro_headlines = [item.headline for item in market_data.get_market_news(lookback_hours=18)]
        except Exception:  # noqa: BLE001 -- sector context is a nice-to-have, not worth failing the scan over
            logger.exception("Failed to fetch general market news for sector attribution")

    for sector in GICS_SECTORS:
        moves = sector_moves.get(sector, [])
        if not moves:
            db.add(SectorOverview(scan_date=today, sector_name=sector, pct_change=0.0, driver_type="none"))
            continue

        sector_pct_change = sum(pct for _, pct in moves) / len(moves)
        top_ticker, top_pct = max(moves, key=lambda m: abs(m[1]))

        top_mover_headline = None
        try:
            top_mover_news = _cached_combined_news(
                market_data, fundamentals, news_cache, top_ticker, lookback_hours=48, today=today
            )
            top_mover_headline = pick_best_headline(top_mover_news)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to fetch news for sector top mover %s", top_ticker)

        driver = attribute_sector_driver(
            sector_name=sector,
            sector_pct_change=sector_pct_change,
            top_mover_ticker=top_ticker,
            top_mover_pct_change=top_pct,
            top_mover_headline=top_mover_headline,
            macro_headlines=macro_headlines,
        )
        db.add(
            SectorOverview(
                scan_date=today,
                sector_name=sector,
                pct_change=sector_pct_change,
                driver_type=driver.driver_type,
                driver_summary=driver.summary,
            )
        )
