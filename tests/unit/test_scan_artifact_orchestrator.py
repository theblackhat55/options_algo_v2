from datetime import date
from pathlib import Path

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.scan_artifact_orchestrator import (
    build_and_write_scan_artifact,
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


def test_build_and_write_scan_artifact_with_explicit_run_id(
    tmp_path: Path,
) -> None:
    decisions = [_make_passed_decision()]

    result = build_and_write_scan_artifact(
        decisions=decisions,
        base_dir=tmp_path,
        run_id="scan_test_001",
    )

    assert result.scan_result.run_id == "scan_test_001"
    assert result.output_path == tmp_path / "scan_test_001.json"
    assert result.output_path.exists()
    assert result.scan_result.summary.total_candidates == 1
    assert result.scan_result.summary.total_passed == 1


def test_build_and_write_scan_artifact_generates_run_id(
    tmp_path: Path,
) -> None:
    decisions = [_make_passed_decision()]

    result = build_and_write_scan_artifact(
        decisions=decisions,
        base_dir=tmp_path,
    )

    assert result.scan_result.run_id.startswith("scan_")
    assert result.output_path.exists()
