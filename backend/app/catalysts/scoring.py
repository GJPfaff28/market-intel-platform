"""Catalyst/'in play' detection engine (PLANNING.md catalyst philosophy).

Not a flat checklist: every tag carries scheduled-vs-unscheduled, a float-size
amplification note, and a "priced in" flag when the stock already ran hard into a
known scheduled event.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from app.data_providers.base import AnalystAction, DailyBar, EarningsEvent, NewsItem

PRICED_IN_RUNUP_LOOKBACK_DAYS = 10
PRICED_IN_RUNUP_THRESHOLD_PCT = 0.15  # 15%+ run-up into a known event = "already priced in"

LOW_FLOAT_SHARES = 20_000_000
HIGH_FLOAT_SHARES = 300_000_000

_KEYWORD_CATEGORIES: list[tuple[str, tuple[str, ...]]] = [
    ("ma", ("acquire", "acquisition", "merger", "merge", "buyout", "takeover")),
    ("fda", ("fda", "clinical trial", "pdufa", "approval", "phase 3", "phase iii")),
    ("short_report", ("short seller", "short-seller", "short report", "hindenburg", "muddy waters")),
    ("guidance", ("guidance", "outlook cut", "outlook raised", "preannounce")),
    ("halt", ("trading halt", "halted")),
    ("offering", ("secondary offering", "share offering", "dilution", "pricing of")),
]


@dataclass
class CatalystResult:
    kind: str  # "scheduled" | "unscheduled"
    category: str
    summary: str
    priced_in_flag: bool = False


def float_context(float_shares: float | None) -> str:
    if float_shares is None:
        return "float unknown"
    if float_shares < LOW_FLOAT_SHARES:
        return f"low float (~{float_shares / 1_000_000:.1f}M shares) — amplifies the move"
    if float_shares > HIGH_FLOAT_SHARES:
        return f"large float (~{float_shares / 1_000_000:.0f}M shares) — dampens the move"
    return f"moderate float (~{float_shares / 1_000_000:.0f}M shares)"


def _categorize_headline(headline: str) -> str:
    text = headline.lower()
    for category, keywords in _KEYWORD_CATEGORIES:
        if any(kw in text for kw in keywords):
            return category
    return "other"


def _mentions_ticker(item: NewsItem) -> bool:
    """Does the article's own text actually name this ticker, as opposed to just
    being in Alpaca's (often loose/mistagged) symbols list for the request? This
    catches cases like a "$6.51 Diesel..." economy article that Alpaca returns for
    META's news query despite never mentioning Meta anywhere in the text -- a much
    more reliable relevance signal than the symbol-count heuristic alone.
    """
    pattern = re.compile(rf"\b{re.escape(item.ticker)}\b", re.IGNORECASE)
    return bool(pattern.search(item.headline) or pattern.search(item.summary))


def _is_priced_in(bars: list[DailyBar]) -> bool:
    if len(bars) < PRICED_IN_RUNUP_LOOKBACK_DAYS + 1:
        return False
    window = bars[-(PRICED_IN_RUNUP_LOOKBACK_DAYS + 1) :]
    start_close, end_close = window[0].close, window[-1].close
    if start_close <= 0:
        return False
    run_up = (end_close - start_close) / start_close
    return run_up >= PRICED_IN_RUNUP_THRESHOLD_PCT


def build_catalyst_tags(
    *,
    today: dt.date,
    bars: list[DailyBar],
    news_items: list[NewsItem],
    earnings_events: list[EarningsEvent],
    analyst_actions: list[AnalystAction],
) -> list[CatalystResult]:
    tags: list[CatalystResult] = []

    for event in earnings_events:
        if event.date != today:
            continue
        priced_in = _is_priced_in(bars)
        when_label = {"bmo": "before market open", "amc": "after market close"}.get(event.when, "today")
        summary = f"Earnings {when_label}"
        if event.eps_estimate is not None:
            summary += f" (EPS est. {event.eps_estimate:.2f})"
        if priced_in:
            summary += " — stock already ran into this event, may be priced in"
        tags.append(CatalystResult(kind="scheduled", category="earnings", summary=summary, priced_in_flag=priced_in))

    for action in analyst_actions:
        summary = f"{action.firm}: {action.action}"
        if action.from_grade and action.to_grade:
            summary += f" ({action.from_grade} -> {action.to_grade})"
        tags.append(CatalystResult(kind="unscheduled", category="analyst", summary=summary))

    # Prefer genuinely relevant articles over broad multi-symbol roundups and
    # mistagged pieces ("10 Health Care Stocks Whale Activity...", a diesel-prices
    # economy article that never mentions the company). Sort key, in priority
    # order: (1) does the article's own text actually name this ticker -- the
    # strongest signal, since Alpaca's symbol tagging alone proved unreliable;
    # (2) fewer tagged symbols = more likely a single-stock article, not a
    # roundup; (3) most recent first among equally relevant items.
    sorted_news = sorted(
        news_items,
        key=lambda item: (0 if _mentions_ticker(item) else 1, item.tagged_symbol_count, -item.published_at.timestamp()),
    )

    for item in sorted_news:
        relevant = _mentions_ticker(item)
        category = _categorize_headline(item.headline)
        summary = item.headline if relevant else f"{item.headline} (general market news, not company-specific)"
        tags.append(
            CatalystResult(
                kind="unscheduled",
                category=category if relevant else "market_wide",
                summary=summary,
            )
        )

    return tags
