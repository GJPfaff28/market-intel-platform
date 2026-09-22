"""Small, dependency-free technical indicator helpers (no numpy/pandas needed for
a single-ticker-at-a-time computation at this scale)."""

from __future__ import annotations

import statistics

from app.data_providers.base import DailyBar


def true_range(bar: DailyBar, prev_close: float) -> float:
    return max(bar.high - bar.low, abs(bar.high - prev_close), abs(bar.low - prev_close))


def atr(bars: list[DailyBar], period: int = 14) -> float:
    """Average True Range over the last `period` bars. Needs period+1 bars since
    each true-range value depends on the prior bar's close."""
    if len(bars) < period + 1:
        return 0.0
    window = bars[-(period + 1) :]
    true_ranges = [true_range(window[i], window[i - 1].close) for i in range(1, len(window))]
    return sma(true_ranges)


def ema(values: list[float], span: int) -> list[float]:
    if not values:
        return []
    k = 2 / (span + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(v * k + result[-1] * (1 - k))
    return result


def sma(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def bollinger_bands(values: list[float], window: int = 20, num_std: float = 2.0) -> tuple[float, float, float]:
    """Returns (lower_band, sma, upper_band) using the last `window` values."""
    window_values = values[-window:]
    mid = sma(window_values)
    std = statistics.pstdev(window_values) if len(window_values) > 1 else 0.0
    return mid - num_std * std, mid, mid + num_std * std
