"""Setup 2: Day 2 / Day 3 Continuation (PLANNING.md, Setup 2).

Day 1 qualifying event (either qualifies): a big % gainer on volume (4% for large
caps >= $2B market cap, 8% for small caps), OR a breakout day (Setup 1's definition).
Continuation confirmation: Day 2 (or Day 3) must print a HIGHER LOW than Day 1.
Window: strictly Day 2-3 only, Day 4+ excluded.

Implementation note: this scan runs pre-market, before "today"'s bar exists, so the
higher-low confirmation can only be checked against *completed* bars. That means:
  - If yesterday (bars[-1]) was Day 1, today would be Day 2 -- but the higher-low
    confirmation is still pending (today hasn't happened), so this is a "Setting Up"
    near-miss, not a confirmed match.
  - If two sessions ago (bars[-2]) was Day 1 and yesterday (bars[-1]) already printed
    a higher low than Day 1, Day 2 is confirmed and today is a Day 3 candidate -- a
    full setup match.
"""

from __future__ import annotations

from app.data_providers.base import DailyBar
from app.db.models import SetupType, Timeframe
from app.setups.base import NearMissResult, SetupMatchResult
from app.setups.momentum_breakout import CONSOLIDATION_LOOKBACK_DAYS

LARGE_CAP_THRESHOLD_USD = 2_000_000_000
LARGE_CAP_DAY1_PCT = 0.04
SMALL_CAP_DAY1_PCT = 0.08


def _day1_threshold(market_cap: float | None) -> float:
    if market_cap is not None and market_cap >= LARGE_CAP_THRESHOLD_USD:
        return LARGE_CAP_DAY1_PCT
    return SMALL_CAP_DAY1_PCT


def _is_big_gainer(bar: DailyBar, prev_bar: DailyBar, market_cap: float | None) -> bool:
    if prev_bar.close <= 0:
        return False
    pct_move = (bar.close - prev_bar.close) / prev_bar.close
    return pct_move >= _day1_threshold(market_cap)


def _is_breakout_day(bars: list[DailyBar], index: int) -> bool:
    """Was bars[index] a Setup-1-style breakout day, using only bars before it?"""
    if index < CONSOLIDATION_LOOKBACK_DAYS:
        return False
    window = bars[index - CONSOLIDATION_LOOKBACK_DAYS : index]
    range_high = max(b.high for b in window)
    return bars[index].close > range_high


def _is_day1(bars: list[DailyBar], index: int, market_cap: float | None) -> bool:
    if index < 1:
        return False
    return _is_big_gainer(bars[index], bars[index - 1], market_cap) or _is_breakout_day(bars, index)


def check_day2_3(bars: list[DailyBar], market_cap: float | None) -> SetupMatchResult | None:
    if len(bars) < CONSOLIDATION_LOOKBACK_DAYS + 3:
        return None

    last_idx = len(bars) - 1  # yesterday (most recently completed session)
    day1_idx = last_idx - 1  # two sessions ago

    if not _is_day1(bars, day1_idx, market_cap):
        return None

    day1_bar = bars[day1_idx]
    day2_bar = bars[last_idx]  # yesterday = Day 2, confirmed
    if day2_bar.low <= day1_bar.low:
        return None  # no higher low -> continuation not confirmed

    return SetupMatchResult(
        setup_type=SetupType.DAY_2_3,
        timeframe=Timeframe.SWING,
        day_number=3,  # today, pre-market, is the Day 3 candidate
        detail=(
            f"Day 1 on {day1_bar.date.isoformat()} (${day1_bar.close:.2f}), "
            f"Day 2 higher low confirmed (${day2_bar.low:.2f} > ${day1_bar.low:.2f}); "
            "today is a Day 3 continuation candidate"
        ),
    )


def check_near_miss(bars: list[DailyBar], market_cap: float | None) -> NearMissResult | None:
    """Yesterday qualified as Day 1 -- today WOULD be Day 2, pending the higher-low
    confirmation that can only happen once today's session completes."""
    if len(bars) < CONSOLIDATION_LOOKBACK_DAYS + 2:
        return None
    last_idx = len(bars) - 1
    if not _is_day1(bars, last_idx, market_cap):
        return None
    day1_bar = bars[last_idx]
    return NearMissResult(
        setup_type=SetupType.DAY_2_3,
        proximity_pct=0.0,  # binary: qualifies as a Day-2 watch, or it doesn't
        detail=(
            f"Day 1 confirmed yesterday ({day1_bar.date.isoformat()}, ${day1_bar.close:.2f}); "
            f"watching for a higher low today to confirm Day 2 (needs low > ${day1_bar.low:.2f})"
        ),
    )
