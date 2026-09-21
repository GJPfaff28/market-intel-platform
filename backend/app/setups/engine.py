from __future__ import annotations

from app.data_providers.base import DailyBar
from app.setups import day2_3, momentum_breakout
from app.setups.base import NearMissResult, SetupMatchResult

# Reversal/Mean-Reversion is intentionally not evaluated -- disabled per user
# request to focus only on Momentum/Breakout and Day 2/3 Continuation. The
# module (app/setups/reversal.py) is left in place, tested and working, in case
# it's wanted back later; it's just not called from here.


def evaluate_setups(bars: list[DailyBar], market_cap: float | None) -> list[SetupMatchResult]:
    matches = []
    for result in (
        momentum_breakout.check_momentum_breakout(bars),
        day2_3.check_day2_3(bars, market_cap),
    ):
        if result is not None:
            matches.append(result)
    return matches


def evaluate_near_misses(bars: list[DailyBar], market_cap: float | None) -> list[NearMissResult]:
    near_misses = []
    for result in (
        momentum_breakout.check_near_miss(bars),
        day2_3.check_near_miss(bars, market_cap),
    ):
        if result is not None:
            near_misses.append(result)
    return near_misses
