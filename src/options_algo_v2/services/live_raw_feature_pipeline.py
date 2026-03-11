from __future__ import annotations

from datetime import date

from options_algo_v2.domain.historical_row_provider import HistoricalRowProvider
from options_algo_v2.domain.raw_features import RawFeatureInput
from options_algo_v2.services.historical_feature_pipeline import (
    build_raw_feature_input_from_bar_rows,
)


def build_live_raw_feature_input_from_rows(
    *,
    symbol: str,
    rows: list[dict[str, object]],
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
    return build_raw_feature_input_from_bar_rows(
        symbol=symbol,
        rows=rows,
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


def build_live_raw_feature_input(
    *,
    symbol: str,
    dataset: str,
    schema: str,
    provider: HistoricalRowProvider,
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
    rows = provider.get_bar_rows(
        symbol=symbol,
        dataset=dataset,
        schema=schema,
    )

    return build_live_raw_feature_input_from_rows(
        symbol=symbol,
        rows=rows,
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
