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


def _directional_movement(
    current_bar: BarData,
    previous_bar: BarData,
) -> tuple[float, float]:
    up_move = current_bar.high - previous_bar.high
    down_move = previous_bar.low - current_bar.low

    plus_dm = 0.0
    minus_dm = 0.0

    if up_move > down_move and up_move > 0.0:
        plus_dm = up_move
    if down_move > up_move and down_move > 0.0:
        minus_dm = down_move

    return plus_dm, minus_dm


def compute_adx14(bars: list[BarData]) -> float:
    if len(bars) < 29:
        raise ValueError("need at least 29 bars to compute ADX14")

    true_ranges: list[float] = []
    plus_dms: list[float] = []
    minus_dms: list[float] = []

    for index in range(1, len(bars)):
        current_bar = bars[index]
        previous_bar = bars[index - 1]

        true_ranges.append(_true_range(current_bar, previous_bar.close))
        plus_dm, minus_dm = _directional_movement(current_bar, previous_bar)
        plus_dms.append(plus_dm)
        minus_dms.append(minus_dm)

    period = 14

    if len(true_ranges) < (2 * period):
        raise ValueError("need at least 28 directional periods to compute ADX14")

    tr14 = sum(true_ranges[:period])
    plus_dm14 = sum(plus_dms[:period])
    minus_dm14 = sum(minus_dms[:period])

    dx_values: list[float] = []

    for index in range(period, len(true_ranges)):
        if index > period:
            tr14 = tr14 - (tr14 / period) + true_ranges[index]
            plus_dm14 = plus_dm14 - (plus_dm14 / period) + plus_dms[index]
            minus_dm14 = minus_dm14 - (minus_dm14 / period) + minus_dms[index]

        if tr14 <= 0.0:
            plus_di = 0.0
            minus_di = 0.0
        else:
            plus_di = 100.0 * (plus_dm14 / tr14)
            minus_di = 100.0 * (minus_dm14 / tr14)

        di_sum = plus_di + minus_di
        if di_sum <= 0.0:
            dx = 0.0
        else:
            dx = 100.0 * abs(plus_di - minus_di) / di_sum

        dx_values.append(dx)

    if len(dx_values) < period:
        raise ValueError("need at least 14 DX values to compute ADX14")

    adx = sum(dx_values[:period]) / period
    for dx in dx_values[period:]:
        adx = ((adx * (period - 1)) + dx) / period

    return adx


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
        adx14=compute_adx14(bars),
    )
