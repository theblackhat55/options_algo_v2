from __future__ import annotations

from datetime import date

from options_algo_v2.domain.computed_features import ComputedUnderlyingFeatures
from options_algo_v2.domain.raw_features import RawFeatureInput


def build_raw_feature_input(
    *,
    symbol: str,
    computed_features: ComputedUnderlyingFeatures,
    adx14: float | None = None,
    iv_rank: float,
    iv_hv_ratio: float,
    avg_daily_volume: float,
    option_open_interest: int,
    option_volume: int,
    bid: float,
    ask: float,
    option_quote_age_seconds: int,
    underlying_quote_age_seconds: int,
    market_breadth_pct_above_20dma: float,
    earnings_date: date | None,
    entry_date: date,
    dte_days: int,
) -> RawFeatureInput:
    resolved_adx14 = computed_features.adx14 if adx14 is None else adx14

    return RawFeatureInput(
        symbol=symbol,
        close=computed_features.close,
        dma20=computed_features.dma20,
        dma50=computed_features.dma50,
        atr20=computed_features.atr20,
        adx14=resolved_adx14,
        iv_rank=iv_rank,
        iv_hv_ratio=iv_hv_ratio,
        avg_daily_volume=avg_daily_volume,
        option_open_interest=option_open_interest,
        option_volume=option_volume,
        bid=bid,
        ask=ask,
        option_quote_age_seconds=option_quote_age_seconds,
        underlying_quote_age_seconds=underlying_quote_age_seconds,
        market_breadth_pct_above_20dma=market_breadth_pct_above_20dma,
        earnings_date=earnings_date,
        entry_date=entry_date,
        dte_days=dte_days,
        rsi14=computed_features.rsi14,
        five_day_return=computed_features.five_day_return,
        breakout_above_20d_high=computed_features.breakout_above_20d_high,
        breakdown_below_20d_low=computed_features.breakdown_below_20d_low,
        breakout_volume_multiple=computed_features.breakout_volume_multiple,
    )
