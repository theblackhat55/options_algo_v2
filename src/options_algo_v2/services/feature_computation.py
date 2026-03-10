from __future__ import annotations

from options_algo_v2.domain.bar_data import BarData
from options_algo_v2.domain.computed_features import ComputedUnderlyingFeatures


def compute_sma(values: list[float], period: int) -> float:
    if period <= 0:
        raise ValueError("period must be positive")

    if len(values) < period:
        raise ValueError(f"need at least {period} values to compute SMA")

    window = values[-period:]
    return sum(window) / period


def _true_range(current_bar: BarData, previous_close: float) -> float:
    intraday_range = current_bar.high - current_bar.low
    high_gap = abs(current_bar.high - previous_close)
    low_gap = abs(current_bar.low - previous_close)
    return max(intraday_range, high_gap, low_gap)


def compute_atr20(bars: list[BarData]) -> float:
    if len(bars) < 21:
        raise ValueError("need at least 21 bars to compute ATR20")

    true_ranges: list[float] = []

    for index in range(1, len(bars)):
        current_bar = bars[index]
        previous_close = bars[index - 1].close
        true_ranges.append(_true_range(current_bar, previous_close))

    if len(true_ranges) < 20:
        raise ValueError("need at least 20 true ranges to compute ATR20")

    return sum(true_ranges[-20:]) / 20.0


def compute_underlying_features(
    bars: list[BarData],
) -> ComputedUnderlyingFeatures:
    if len(bars) < 50:
        raise ValueError("need at least 50 bars to compute underlying features")

    closes = [bar.close for bar in bars]
    latest_close = closes[-1]

    return ComputedUnderlyingFeatures(
        close=latest_close,
        dma20=compute_sma(closes, 20),
        dma50=compute_sma(closes, 50),
        atr20=compute_atr20(bars),
    )
