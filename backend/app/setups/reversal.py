"""Setup 3: Reversal / Mean-Reversion (PLANNING.md, Setup 3).

Trigger (both required together): climactic/exhaustion reversal (a multi-day extended
run showing exhaustion) combined with extension measured via distance from the 8 EMA
and trading outside the 20-day Bollinger Bands. Applies to BOTH directions (oversold
bounce-up and topping-out/fade-down). Daily chart only, no intraday component.

Implementation default: the user specified the *indicators* (8 EMA distance, 20D
Bollinger Bands) but not an exact distance-from-EMA percentage. EMA8_EXTENSION_PCT
below is a reasonable starting default (flagged in PLANNING.md as an implementation
nuance) and should be the first thing to tune once real data is flowing.
"""

from __future__ import annotations

from app.data_providers.base import DailyBar
from app.db.models import SetupType, Timeframe
from app.setups.base import NearMissResult, SetupMatchResult
from app.setups.indicators import bollinger_bands, ema

EMA_SPAN = 8
BOLLINGER_WINDOW = 20
EMA8_EXTENSION_PCT = 0.10  # 10% away from the 8 EMA counts as "extended"
NEAR_MISS_PROXIMITY = 0.03
CLIMACTIC_MIN_MOVE_PCT = 0.05  # the exhaustion day itself should be a notable move


def _compute(bars: list[DailyBar]) -> tuple[float, float, float, float] | None:
    """Returns (last_close, ema8_last, lower_band, upper_band), or None if not enough data."""
    if len(bars) < max(EMA_SPAN, BOLLINGER_WINDOW) + 1:
        return None
    closes = [b.close for b in bars]
    ema8_series = ema(closes, EMA_SPAN)
    lower_band, _, upper_band = bollinger_bands(closes, BOLLINGER_WINDOW)
    return closes[-1], ema8_series[-1], lower_band, upper_band


def check_reversal(bars: list[DailyBar]) -> SetupMatchResult | None:
    computed = _compute(bars)
    if computed is None:
        return None
    last_close, ema8_last, lower_band, upper_band = computed
    last_bar, prev_bar = bars[-1], bars[-2]
    day_move_pct = abs(last_bar.close - prev_bar.close) / prev_bar.close if prev_bar.close else 0
    ema_distance_pct = (last_close - ema8_last) / ema8_last if ema8_last else 0

    is_climactic = day_move_pct >= CLIMACTIC_MIN_MOVE_PCT

    if last_close > upper_band and ema_distance_pct >= EMA8_EXTENSION_PCT and is_climactic:
        return SetupMatchResult(
            setup_type=SetupType.REVERSAL,
            timeframe=Timeframe.SWING,
            detail=(
                f"topping/fade candidate: {ema_distance_pct * 100:.1f}% above 8 EMA, "
                f"above upper 20D Bollinger Band (${upper_band:.2f}), "
                f"climactic {day_move_pct * 100:.1f}% move"
            ),
        )

    if last_close < lower_band and ema_distance_pct <= -EMA8_EXTENSION_PCT and is_climactic:
        return SetupMatchResult(
            setup_type=SetupType.REVERSAL,
            timeframe=Timeframe.SWING,
            detail=(
                f"oversold bounce candidate: {abs(ema_distance_pct) * 100:.1f}% below 8 EMA, "
                f"below lower 20D Bollinger Band (${lower_band:.2f}), "
                f"climactic {day_move_pct * 100:.1f}% move"
            ),
        )

    return None


def check_near_miss(bars: list[DailyBar]) -> NearMissResult | None:
    computed = _compute(bars)
    if computed is None:
        return None
    last_close, ema8_last, lower_band, upper_band = computed
    ema_distance_pct = (last_close - ema8_last) / ema8_last if ema8_last else 0

    if last_close <= upper_band and ema_distance_pct > 0:
        proximity = (upper_band - last_close) / upper_band if upper_band else 1
        if proximity <= NEAR_MISS_PROXIMITY:
            return NearMissResult(
                setup_type=SetupType.REVERSAL,
                proximity_pct=proximity,
                detail=f"{proximity * 100:.1f}% below upper Bollinger Band, extending above 8 EMA",
            )

    if last_close >= lower_band and ema_distance_pct < 0:
        proximity = (last_close - lower_band) / lower_band if lower_band else 1
        if proximity <= NEAR_MISS_PROXIMITY:
            return NearMissResult(
                setup_type=SetupType.REVERSAL,
                proximity_pct=proximity,
                detail=f"{proximity * 100:.1f}% above lower Bollinger Band, extending below 8 EMA",
            )

    return None
