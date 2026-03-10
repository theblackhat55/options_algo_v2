import json
from datetime import date
from pathlib import Path

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.scan_result_builder import build_scan_result
from options_algo_v2.services.scan_result_writer import (
    build_scan_result_path,
    write_scan_result,
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


def test_build_scan_result_path_returns_expected_path(tmp_path: Path) -> None:
    path = build_scan_result_path(
        run_id="run_test_001",
        base_dir=tmp_path,
    )

    assert path == tmp_path / "run_test_001.json"


def test_write_scan_result_creates_json_file(tmp_path: Path) -> None:
    decisions = [_make_passed_decision()]
    scan_result = build_scan_result(
        run_id="run_test_001",
        decisions=decisions,
    )

    output_path = write_scan_result(
        scan_result=scan_result,
        base_dir=tmp_path,
    )

    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run_test_001"
    assert payload["summary"]["total_candidates"] == 1
    assert payload["summary"]["total_passed"] == 1
    assert payload["decisions"][0]["symbol"] == "AAPL"
