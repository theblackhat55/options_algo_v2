from datetime import date

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.scan_result_builder import (
    build_scan_result,
    build_scan_summary,
)


def _make_passed_decision():
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
    return evaluate_candidate_decision(evaluation_input)


def _make_rejected_decision():
    evaluation_input = CandidateEvaluationInput(
        symbol="SPY",
        market_regime=MarketRegime.RANGE_UNCLEAR,
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
    return evaluate_candidate_decision(evaluation_input)


def test_build_scan_summary_counts_passed_and_rejected() -> None:
    decisions = [_make_passed_decision(), _make_rejected_decision()]
    summary = build_scan_summary(decisions)

    assert summary.total_candidates == 2
    assert summary.total_passed == 1
    assert summary.total_rejected == 1
    assert summary.passed_symbols == ["AAPL"]
    assert summary.rejected_symbols == ["SPY"]


def test_build_scan_result_returns_expected_structure() -> None:
    decisions = [_make_passed_decision(), _make_rejected_decision()]
    result = build_scan_result(
        run_id="run_test_001",
        decisions=decisions,
    )

    assert result.run_id == "run_test_001"
    assert result.generated_at
    assert result.config_versions["strategy"] == "strategy_v1"
    assert result.config_versions["risk"] == "risk_v1"
    assert result.summary.total_candidates == 2
    assert len(result.decisions) == 2
    assert result.decisions[0]["symbol"] == "AAPL"
    assert result.decisions[1]["symbol"] == "SPY"
