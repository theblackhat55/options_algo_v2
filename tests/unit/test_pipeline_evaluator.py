from datetime import date

from options_algo_v2.domain.enums import (
    DirectionalState,
    IVState,
    MarketRegime,
    SignalState,
    StrategyType,
)
from options_algo_v2.domain.pipeline_payload import PipelineEvaluationPayload
from options_algo_v2.services.pipeline_evaluator import (
    evaluate_pipeline_payload,
    payload_to_evaluation_input,
)


def test_payload_to_evaluation_input_maps_fields_correctly() -> None:
    payload = PipelineEvaluationPayload(
        symbol="AAPL",
        market_regime=MarketRegime.TREND_UP,
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
        earnings_date=None,
        planned_latest_exit=date(2026, 3, 20),
        underlying_price=150.0,
        avg_daily_volume=5_000_000,
        option_open_interest=2_000,
        option_volume=400,
        bid=2.45,
        ask=2.55,
        option_quote_age_seconds=10,
        underlying_quote_age_seconds=2,
        close=102.0,
        dma20=100.0,
        atr20=2.0,
        adx14=40.0,
        iv_hv_ratio=1.50,
        market_breadth_pct_above_20dma=65.0,
        expected_move_fit=True,
    )

    evaluation_input = payload_to_evaluation_input(payload)

    assert evaluation_input.symbol == payload.symbol
    assert evaluation_input.market_regime == payload.market_regime
    assert evaluation_input.directional_state == payload.directional_state
    assert evaluation_input.iv_state == payload.iv_state
    assert evaluation_input.expected_move_fit == payload.expected_move_fit


def test_evaluate_pipeline_payload_returns_qualified_decision() -> None:
    payload = PipelineEvaluationPayload(
        symbol="AAPL",
        market_regime=MarketRegime.TREND_UP,
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
        earnings_date=None,
        planned_latest_exit=date(2026, 3, 20),
        underlying_price=150.0,
        avg_daily_volume=5_000_000,
        option_open_interest=2_000,
        option_volume=400,
        bid=2.45,
        ask=2.55,
        option_quote_age_seconds=10,
        underlying_quote_age_seconds=2,
        close=102.0,
        dma20=100.0,
        atr20=2.0,
        adx14=40.0,
        iv_hv_ratio=1.50,
        market_breadth_pct_above_20dma=65.0,
        expected_move_fit=True,
    )

    decision = evaluate_pipeline_payload(payload)

    assert decision.candidate.signal_state == SignalState.QUALIFIED
    assert decision.candidate.strategy_type == StrategyType.BULL_PUT_SPREAD
    assert decision.final_passed is True
    assert decision.final_score == 100.0


def test_evaluate_pipeline_payload_returns_rejected_decision() -> None:
    # NEUTRAL directional state is always rejected
    payload = PipelineEvaluationPayload(
        symbol="SPY",
        market_regime=MarketRegime.TREND_UP,
        directional_state=DirectionalState.NEUTRAL,
        iv_state=IVState.IV_RICH,
        earnings_date=None,
        planned_latest_exit=date(2026, 3, 20),
        underlying_price=150.0,
        avg_daily_volume=5_000_000,
        option_open_interest=2_000,
        option_volume=400,
        bid=2.45,
        ask=2.55,
        option_quote_age_seconds=10,
        underlying_quote_age_seconds=2,
        close=102.0,
        dma20=100.0,
        atr20=2.0,
        adx14=40.0,
        iv_hv_ratio=1.50,
        market_breadth_pct_above_20dma=65.0,
        expected_move_fit=True,
    )

    decision = evaluate_pipeline_payload(payload)

    assert decision.candidate.signal_state == SignalState.REJECTED
    assert decision.final_passed is False
    assert decision.rejection_reasons
