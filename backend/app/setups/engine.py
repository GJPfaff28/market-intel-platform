from __future__ import annotations

from app.data_providers.base import DailyBar
from app.setups import day2_3, momentum_breakout, reversal
from app.setups.base import NearMissResult, SetupMatchResult


def evaluate_setups(bars: list[DailyBar], market_cap: float | None) -> list[SetupMatchResult]:
    matches = []
    for result in (
        momentum_breakout.check_momentum_breakout(bars),
        day2_3.check_day2_3(bars, market_cap),
        reversal.check_reversal(bars),
    ):
        if result is not None:
            matches.append(result)
    return matches


def evaluate_near_misses(bars: list[DailyBar], market_cap: float | None) -> list[NearMissResult]:
    near_misses = []
    for result in (
        momentum_breakout.check_near_miss(bars),
        day2_3.check_near_miss(bars, market_cap),
        reversal.check_near_miss(bars),
    ):
        if result is not None:
            near_misses.append(result)
    return near_misses
