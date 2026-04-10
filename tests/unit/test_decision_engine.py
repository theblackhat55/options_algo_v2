from datetime import date

from options_algo_v2.domain.enums import (
    DirectionalState,
    IVState,
    MarketRegime,
    SignalState,
    StrategyType,
)
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision


def test_decision_engine_returns_passed_candidate() -> None:
    evaluation_input = CandidateEvaluationInput(
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

    decision = evaluate_candidate_decision(evaluation_input)

    assert decision.candidate.signal_state == SignalState.QUALIFIED
    assert decision.candidate.strategy_type == StrategyType.BULL_PUT_SPREAD
    assert decision.final_passed is True
    assert decision.final_score == 100.0
    assert decision.min_score_required == 70.0
    assert decision.rejection_reasons == []


def test_decision_engine_rejects_for_earnings_event() -> None:
    evaluation_input = CandidateEvaluationInput(
        symbol="MSFT",
        market_regime=MarketRegime.TREND_UP,
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
        earnings_date=date(2026, 3, 19),
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

    decision = evaluate_candidate_decision(evaluation_input)

    assert decision.final_passed is False
    assert "earnings event occurs before planned exit" in decision.rejection_reasons


def test_decision_engine_rejects_for_liquidity_failure() -> None:
    evaluation_input = CandidateEvaluationInput(
        symbol="TSLA",
        market_regime=MarketRegime.TREND_DOWN,
        directional_state=DirectionalState.BEARISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
        earnings_date=None,
        planned_latest_exit=date(2026, 3, 20),
        underlying_price=15.0,
        avg_daily_volume=100_000,
        option_open_interest=100,
        option_volume=20,
        bid=1.00,
        ask=1.20,
        option_quote_age_seconds=120,
        underlying_quote_age_seconds=20,
        close=98.0,
        dma20=100.0,
        atr20=2.0,
        adx14=40.0,
        iv_hv_ratio=1.50,
        market_breadth_pct_above_20dma=65.0,
        expected_move_fit=True,
    )

    decision = evaluate_candidate_decision(evaluation_input)

    assert decision.final_passed is False
    assert len(decision.rejection_reasons) > 0


def test_decision_engine_rejects_for_extension_failure() -> None:
    # close=105.0, dma20=100.0, atr20=2.0, extension_atr_multiple=2.0
    # 105 - 100 = 5.0 > 2.0 * 2.0 = 4.0 → clearly extended
    evaluation_input = CandidateEvaluationInput(
        symbol="NVDA",
        market_regime=MarketRegime.TREND_UP,
        directional_state=DirectionalState.BULLISH_BREAKOUT,
        iv_state=IVState.IV_NORMAL,
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
        close=105.0,
        dma20=100.0,
        atr20=2.0,
        adx14=40.0,
        iv_hv_ratio=1.50,
        market_breadth_pct_above_20dma=65.0,
        expected_move_fit=True,
    )

    decision = evaluate_candidate_decision(evaluation_input)

    assert decision.final_passed is False
    assert "bullish setup is too extended above 20 dma" in decision.rejection_reasons


def test_decision_engine_returns_zero_score_for_selector_rejection() -> None:
    # NEUTRAL directional state is always rejected regardless of regime
    evaluation_input = CandidateEvaluationInput(
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

    decision = evaluate_candidate_decision(evaluation_input)

    assert decision.candidate.signal_state == SignalState.REJECTED
    assert decision.final_passed is False
    assert decision.final_score == 0.0
    assert decision.rejection_reasons
