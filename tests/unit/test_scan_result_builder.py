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
    assert summary.rejection_reason_counts == {
        "market regime does not permit new entries": 1,
    }
    assert summary.signal_state_counts == {"QUALIFIED": 1, "REJECTED": 1}
    assert summary.strategy_type_counts == {
        "BULL_CALL_SPREAD": 1,
        "BULL_PUT_SPREAD": 1,
    }


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
    assert result.runtime_metadata["runtime_mode"] == "mock"
    assert result.runtime_metadata["databento"] == {
        "dataset": "XNAS.ITCH",
        "schema": "ohlcv-1d",
        "has_api_key": "false",
    }
    assert result.runtime_metadata["historical_row_provider"] == "mock"
    assert result.runtime_metadata["market_breadth_provider"] == "mock"
    assert result.runtime_metadata["market_breadth_provider_source"] == "mock"
    assert result.runtime_metadata[
        "feature_source_counts_by_historical_row_provider"
    ] == {"mock": 2}
    assert result.runtime_metadata[
        "feature_source_counts_by_market_breadth_provider"
    ] == {"mock": 2}
    assert result.runtime_metadata[
        "feature_source_counts_by_dataset_schema"
    ] == {"XNAS.ITCH|ohlcv-1d": 2}
    assert result.runtime_metadata["trade_candidate_counts_by_strategy_family"] == {
        "BULL_PUT_SPREAD": 1
    }
    assert result.runtime_metadata["trade_candidate_counts_by_symbol"] == {"AAPL": 1}
    assert result.runtime_metadata["top_trade_candidate_symbols"] == ["AAPL"]
    assert len(result.runtime_metadata["top_trade_summary_rows"]) == 1
    assert result.runtime_metadata["top_trade_summary_rows"][0]["symbol"] == "AAPL"
    assert result.summary.total_candidates == 2
    assert result.summary.rejection_reason_counts == {
        "market regime does not permit new entries": 1,
    }
    assert result.summary.signal_state_counts == {"QUALIFIED": 1, "REJECTED": 1}
    assert result.summary.strategy_type_counts == {
        "BULL_CALL_SPREAD": 1,
        "BULL_PUT_SPREAD": 1,
    }
    assert len(result.decisions) == 2
    assert result.decisions[0]["symbol"] == "AAPL"
    assert result.decisions[1]["symbol"] == "SPY"
