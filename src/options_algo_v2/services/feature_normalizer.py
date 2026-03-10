from __future__ import annotations

from datetime import timedelta

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.pipeline_payload import PipelineEvaluationPayload
from options_algo_v2.domain.raw_features import RawFeatureInput


def normalize_raw_features_to_payload(
    raw: RawFeatureInput,
) -> PipelineEvaluationPayload:
    if raw.market_breadth_pct_above_20dma > 55.0:
        market_regime = MarketRegime.TREND_UP
    elif raw.market_breadth_pct_above_20dma < 45.0:
        market_regime = MarketRegime.TREND_DOWN
    else:
        market_regime = MarketRegime.RANGE_UNCLEAR

    if raw.iv_rank >= 60.0 or raw.iv_hv_ratio >= 1.25:
        iv_state = IVState.IV_RICH
    elif raw.iv_rank <= 30.0 or raw.iv_hv_ratio <= 1.05:
        iv_state = IVState.IV_CHEAP
    else:
        iv_state = IVState.IV_NORMAL

    if raw.close > raw.dma20 > raw.dma50 and raw.adx14 >= 18.0:
        directional_state = DirectionalState.BULLISH_CONTINUATION
    elif raw.close < raw.dma20 < raw.dma50 and raw.adx14 >= 18.0:
        directional_state = DirectionalState.BEARISH_CONTINUATION
    else:
        directional_state = DirectionalState.NEUTRAL

    planned_latest_exit = raw.entry_date + timedelta(days=min(raw.dte_days, 21))

    expected_move_fit = abs(raw.close - raw.dma20) <= (1.5 * raw.atr20)

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
        atr20=raw.atr20,
        expected_move_fit=expected_move_fit,
    )
