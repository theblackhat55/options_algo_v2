from __future__ import annotations

from datetime import date

from options_algo_v2.domain.computed_features import ComputedUnderlyingFeatures
from options_algo_v2.domain.raw_features import RawFeatureInput
from options_algo_v2.services.bar_history_builder import build_bar_data_history
from options_algo_v2.services.feature_computation import compute_underlying_features
from options_algo_v2.services.raw_feature_builder import build_raw_feature_input


def compute_features_from_bar_rows(
    rows: list[dict[str, object]],
) -> ComputedUnderlyingFeatures:
    bars = build_bar_data_history(rows)
    return compute_underlying_features(bars)


def build_raw_feature_input_from_bar_rows(
    *,
    symbol: str,
    rows: list[dict[str, object]],
    adx14: float,
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
    computed_features = compute_features_from_bar_rows(rows)

    return build_raw_feature_input(
        symbol=symbol,
        computed_features=computed_features,
        adx14=adx14,
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
    )
