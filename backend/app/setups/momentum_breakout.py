"""Setup 1: Momentum / Breakout (PLANNING.md, Setup 1).

Breakout reference (either qualifies): top of a multi-day consolidation/range, OR a
52-week/all-time high. Volume confirmation: the scan-wide 2.0x RVOL floor is enough,
no extra bar here. Confirmation: price must CLOSE above the level.

Implementation nuance (flagged in PLANNING.md): this scan runs pre-market, so "close
above the level" is evaluated against the most recently completed daily bar (i.e.
yesterday's close) compared to a reference level computed from the bars before it.
The intraday-trigger half of the rule (confirming the breakout is holding once the
market opens) is a live/frontend concern, not something the pre-market scan can see.
"""

from __future__ import annotations

from app.data_providers.base import DailyBar
from app.db.models import SetupType, Timeframe
from app.setups.base import NearMissResult, SetupMatchResult

CONSOLIDATION_LOOKBACK_DAYS = 20
FIFTY_TWO_WEEK_LOOKBACK_DAYS = 252
NEAR_MISS_PROXIMITY = 0.03  # 3%, per PLANNING.md "tight bar" decision


def check_momentum_breakout(bars: list[DailyBar]) -> SetupMatchResult | None:
    if len(bars) < CONSOLIDATION_LOOKBACK_DAYS + 1:
        return None

    *history, last = bars
    range_high = max(b.high for b in history[-CONSOLIDATION_LOOKBACK_DAYS:])

    reasons = []
    if last.close > range_high:
        reasons.append(f"closed above {CONSOLIDATION_LOOKBACK_DAYS}-day range high (${range_high:.2f})")

    if len(bars) >= FIFTY_TWO_WEEK_LOOKBACK_DAYS:
        fifty_two_week_high = max(b.high for b in bars[:-1][-FIFTY_TWO_WEEK_LOOKBACK_DAYS:])
        if last.close > fifty_two_week_high:
            reasons.append(f"closed above 52-week high (${fifty_two_week_high:.2f})")

    if not reasons:
        return None

    return SetupMatchResult(
        setup_type=SetupType.MOMENTUM_BREAKOUT,
        timeframe=Timeframe.BOTH,  # daily sets it up, intraday triggers it (per PLANNING.md)
        detail="; ".join(reasons),
    )


def check_near_miss(bars: list[DailyBar]) -> NearMissResult | None:
    """Stocks within ~3% of the range-high trigger but not there yet -> 'Setting Up' tab."""
    if len(bars) < CONSOLIDATION_LOOKBACK_DAYS + 1:
        return None
    *history, last = bars
    range_high = max(b.high for b in history[-CONSOLIDATION_LOOKBACK_DAYS:])
    if last.close >= range_high:
        return None  # already broken out, not a near miss
    proximity = (range_high - last.close) / range_high
    if proximity <= NEAR_MISS_PROXIMITY:
        return NearMissResult(
            setup_type=SetupType.MOMENTUM_BREAKOUT,
            proximity_pct=proximity,
            detail=f"{proximity * 100:.1f}% below {CONSOLIDATION_LOOKBACK_DAYS}-day range high (${range_high:.2f})",
        )
    return None
