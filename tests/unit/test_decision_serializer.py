from datetime import date

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.decision_serializer import serialize_candidate_decision


def test_serialize_candidate_decision_for_passed_case() -> None:
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
        expected_move_fit=True,
    )

    decision = evaluate_candidate_decision(evaluation_input)
    payload = serialize_candidate_decision(decision)

    assert payload["symbol"] == "AAPL"
    assert payload["market_regime"] == "TREND_UP"
    assert payload["directional_state"] == "BULLISH_CONTINUATION"
    assert payload["iv_state"] == "IV_RICH"
    assert payload["strategy_type"] == "BULL_PUT_SPREAD"
    assert payload["signal_state"] == "QUALIFIED"
    assert payload["final_passed"] is True
    assert payload["final_score"] == 100.0
    assert payload["min_score_required"] == 70.0
    assert payload["rejection_reasons"] == []


def test_serialize_candidate_decision_for_rejected_case() -> None:
    # NEUTRAL directional state is always rejected
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
        expected_move_fit=True,
    )

    decision = evaluate_candidate_decision(evaluation_input)
    payload = serialize_candidate_decision(decision)

    assert payload["symbol"] == "SPY"
    assert payload["signal_state"] == "REJECTED"
    assert payload["final_passed"] is False
    assert payload["rejection_reasons"]

    event_filter = payload["event_filter"]
    liquidity_filter = payload["liquidity_filter"]
    extension_filter = payload["extension_filter"]

    assert isinstance(event_filter, dict)
    assert isinstance(liquidity_filter, dict)
    assert isinstance(extension_filter, dict)
