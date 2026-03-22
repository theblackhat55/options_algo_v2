from __future__ import annotations

from datetime import timedelta

from options_algo_v2.services.expected_move import compare_expected_moves
from options_algo_v2.classifiers.directional_state import classify_directional_state
from options_algo_v2.classifiers.iv_state import classify_iv_state
from options_algo_v2.classifiers.market_regime import classify_market_regime
from options_algo_v2.domain.features import (
    DirectionalFeatures,
    IVFeatures,
    MarketRegimeFeatures,
)
from options_algo_v2.domain.pipeline_payload import PipelineEvaluationPayload
from options_algo_v2.domain.raw_features import RawFeatureInput


def normalize_raw_features_to_payload(
    raw: RawFeatureInput,
) -> PipelineEvaluationPayload:
    """Convert raw features into a pipeline payload using the canonical classifiers."""

    inferred_vix_defensive = (
        raw.market_breadth_pct_above_20dma < 35.0
        and raw.close < raw.dma20
        and raw.dma20 < raw.dma50
    )

    market_regime = classify_market_regime(
        MarketRegimeFeatures(
            spy_close_above_20dma=raw.close > raw.dma20,
            spy_20dma_above_50dma=raw.dma20 > raw.dma50,
            spy_close_below_20dma=raw.close < raw.dma20,
            spy_20dma_below_50dma=raw.dma20 < raw.dma50,
            breadth_pct_above_20dma=raw.market_breadth_pct_above_20dma,
            vix_defensive=inferred_vix_defensive,
        )
    )

    iv_rv_spread = None
    if raw.iv_hv_ratio is not None:
        iv_rv_spread = (raw.iv_hv_ratio - 1.0) * 100.0

    iv_state = classify_iv_state(
        IVFeatures(
            iv_rank=raw.iv_rank,
            iv_hv_ratio=raw.iv_hv_ratio,
            iv_rv_spread=iv_rv_spread,
        )
    )

    extended_up = (
        raw.close > raw.dma20
        and (raw.close - raw.dma20) > 2.0 * raw.atr20
    )
    extended_down = (
        raw.close < raw.dma20
        and (raw.dma20 - raw.close) > 2.0 * raw.atr20
    )

    directional_state = classify_directional_state(
        DirectionalFeatures(
            close_above_20dma=raw.close > raw.dma20,
            close_above_50dma=raw.close > raw.dma50,
            close_below_20dma=raw.close < raw.dma20,
            close_below_50dma=raw.close < raw.dma50,
            adx=raw.adx14,
            rsi=raw.rsi14 if raw.rsi14 is not None else 50.0,
            five_day_return=raw.five_day_return if raw.five_day_return is not None else 0.0,
            breakout_above_20d_high=raw.breakout_above_20d_high,
            breakdown_below_20d_low=raw.breakdown_below_20d_low,
            breakout_volume_multiple=raw.breakout_volume_multiple,
            extended_up=extended_up,
            extended_down=extended_down,
        )
    )

    planned_latest_exit = raw.entry_date + timedelta(days=min(raw.dte_days, 21))

    expected_move_comparison = compare_expected_moves(
        atm_iv=max(raw.iv_hv_ratio * 0.20, 0.01),
        dte_days=max(min(raw.dte_days, 21), 1),
        atr20=raw.atr20,
        close=raw.close,
    )
    expected_move_fit = expected_move_comparison.edge != "neutral"

    return PipelineEvaluationPayload(
        symbol=raw.symbol,
        market_regime=market_regime,
        directional_state=directional_state,
        iv_state=iv_state,
        earnings_date=raw.earnings_date,
        planned_latest_exit=planned_latest_exit,
        underlying_price=raw.close,
        avg_daily_volume=raw.avg_daily_volume,
        option_open_interest=raw.option_open_interest,
        option_volume=raw.option_volume,
        bid=raw.bid,
        ask=raw.ask,
        option_quote_age_seconds=raw.option_quote_age_seconds,
        underlying_quote_age_seconds=raw.underlying_quote_age_seconds,
        close=raw.close,
        dma20=raw.dma20,
        dma50=raw.dma50,
        atr20=raw.atr20,
        adx14=raw.adx14,
        iv_rank=raw.iv_rank,
        iv_hv_ratio=raw.iv_hv_ratio,
        market_breadth_pct_above_20dma=raw.market_breadth_pct_above_20dma,
        expected_move_fit=expected_move_fit,
        rsi14=raw.rsi14,
        five_day_return=raw.five_day_return,
        breakout_above_20d_high=raw.breakout_above_20d_high,
        breakdown_below_20d_low=raw.breakdown_below_20d_low,
        breakout_volume_multiple=raw.breakout_volume_multiple,
    )
