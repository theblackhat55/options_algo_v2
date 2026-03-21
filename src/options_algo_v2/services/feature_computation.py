from __future__ import annotations

from math import log, sqrt
from statistics import pstdev

from options_algo_v2.domain.bar_data import BarData
from options_algo_v2.domain.computed_features import ComputedUnderlyingFeatures

TRADING_DAYS_PER_YEAR = 252.0


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


def compute_rsi14(bars: list[BarData]) -> float | None:
    if len(bars) < 15:
        return None

    closes = [bar.close for bar in bars]
    gains: list[float] = []
    losses: list[float] = []

    for index in range(len(closes) - 14, len(closes)):
        delta = closes[index] - closes[index - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))

    avg_gain = sum(gains) / 14.0
    avg_loss = sum(losses) / 14.0

    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0.0 else 50.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_five_day_return(bars: list[BarData]) -> float | None:
    if len(bars) < 6:
        return None

    start_close = bars[-6].close
    end_close = bars[-1].close
    if start_close == 0.0:
        return None
    return (end_close - start_close) / start_close


def compute_breakout_above_20d_high(bars: list[BarData]) -> bool:
    if len(bars) < 21:
        return False
    latest_close = bars[-1].close
    prior_20d_high = max(bar.high for bar in bars[-21:-1])
    return latest_close > prior_20d_high


def compute_breakdown_below_20d_low(bars: list[BarData]) -> bool:
    if len(bars) < 21:
        return False
    latest_close = bars[-1].close
    prior_20d_low = min(bar.low for bar in bars[-21:-1])
    return latest_close < prior_20d_low


def compute_breakout_volume_multiple(bars: list[BarData]) -> float:
    if len(bars) < 21:
        return 1.0
    latest_volume = float(bars[-1].volume)
    prior_volumes = [float(bar.volume) for bar in bars[-21:-1]]
    avg_volume = sum(prior_volumes) / len(prior_volumes)
    if avg_volume <= 0.0:
        return 1.0
    return latest_volume / avg_volume


def compute_avg_daily_volume20(bars: list[BarData]) -> float | None:
    if len(bars) < 20:
        return None
    volumes = [float(bar.volume) for bar in bars[-20:]]
    if not volumes:
        return None
    return sum(volumes) / len(volumes)


def compute_hv20_from_bars(bars: list[BarData]) -> float | None:
    if len(bars) < 21:
        return None

    closes = [bar.close for bar in bars if bar.close > 0]
    if len(closes) < 21:
        return None

    log_returns: list[float] = []
    for previous, current in zip(closes[:-1], closes[1:], strict=False):
        if previous <= 0 or current <= 0:
            continue
        log_returns.append(log(current / previous))

    if len(log_returns) < 20:
        return None

    stdev = pstdev(log_returns[-20:])
    return stdev * sqrt(TRADING_DAYS_PER_YEAR)


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
        rsi14=compute_rsi14(bars),
        five_day_return=compute_five_day_return(bars),
        breakout_above_20d_high=compute_breakout_above_20d_high(bars),
        breakdown_below_20d_low=compute_breakdown_below_20d_low(bars),
        breakout_volume_multiple=compute_breakout_volume_multiple(bars),
    )


def compute_feature_rows_for_history(
    *,
    symbol: str,
    bars: list[BarData],
    iv_proxy_by_date: dict[str, float] | None = None,
    feature_version: str = "feature_v1",
    iv_method_version: str = "atm_proxy_v1",
    iv_rank_window: int = 60,
) -> list[dict[str, object]]:
    iv_proxy_by_date = iv_proxy_by_date or {}
    rows: list[dict[str, object]] = []
    iv_history_values: list[float] = []

    for end_index in range(len(bars)):
        window = bars[: end_index + 1]
        bar = window[-1]
        as_of_date = str(bar.timestamp)[:10]

        implied_vol_proxy = iv_proxy_by_date.get(as_of_date)
        if implied_vol_proxy is not None and implied_vol_proxy > 0:
            iv_history_values.append(float(implied_vol_proxy))

        close = float(bar.close)
        dma20 = None
        dma50 = None
        atr20 = None
        adx14 = None
        rsi14 = None
        five_day_return = None
        breakout_above_20d_high = False
        breakdown_below_20d_low = False
        breakout_volume_multiple = 1.0
        avg_daily_volume = compute_avg_daily_volume20(window)
        hv20 = compute_hv20_from_bars(window)
        iv_rank = None
        iv_hv_ratio = None

        closes = [b.close for b in window]

        if len(window) >= 20:
            dma20 = compute_sma(closes, 20)
        if len(window) >= 50:
            dma50 = compute_sma(closes, 50)
        if len(window) >= 21:
            atr20 = compute_atr20(window)
            breakout_above_20d_high = compute_breakout_above_20d_high(window)
            breakdown_below_20d_low = compute_breakdown_below_20d_low(window)
            breakout_volume_multiple = compute_breakout_volume_multiple(window)
        if len(window) >= 29:
            adx14 = compute_adx14(window)
        if len(window) >= 15:
            rsi14 = compute_rsi14(window)
        if len(window) >= 6:
            five_day_return = compute_five_day_return(window)

        if len(iv_history_values) >= iv_rank_window:
            iv_window = iv_history_values[-iv_rank_window:]
            current_iv = iv_window[-1]
            iv_min = min(iv_window)
            iv_max = max(iv_window)
            if iv_max == iv_min:
                iv_rank = 50.0
            elif iv_max > iv_min:
                iv_rank = max(0.0, min(100.0, 100.0 * (current_iv - iv_min) / (iv_max - iv_min)))

        if implied_vol_proxy is not None and hv20 is not None and hv20 > 0:
            iv_hv_ratio = implied_vol_proxy / hv20

        rows.append(
            {
                "symbol": symbol,
                "as_of_date": as_of_date,
                "close": close,
                "dma20": dma20,
                "dma50": dma50,
                "atr20": atr20,
                "adx14": adx14,
                "rsi14": rsi14,
                "five_day_return": five_day_return,
                "breakout_above_20d_high": breakout_above_20d_high,
                "breakdown_below_20d_low": breakdown_below_20d_low,
                "breakout_volume_multiple": breakout_volume_multiple,
                "avg_daily_volume": avg_daily_volume,
                "hv20": hv20,
                "iv_rank": iv_rank,
                "iv_hv_ratio": iv_hv_ratio,
                "feature_version": feature_version,
                "iv_method_version": iv_method_version,
            }
        )

    return rows
