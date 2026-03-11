from __future__ import annotations

import json
from pathlib import Path

from options_algo_v2.services.paper_live_logger import (
    append_paper_live_logs,
    build_run_summary_row,
    build_symbol_rows,
    default_paper_live_log_paths,
)


def _sample_payload() -> dict[str, object]:
    return {
        "run_id": "scan_test_001",
        "summary": {
            "passed_symbols": ["XLE"],
            "rejected_symbols": ["AMD"],
            "rejection_reason_counts": {"directional state is not actionable": 1},
            "signal_state_counts": {"QUALIFIED": 1, "REJECTED": 1},
            "strategy_type_counts": {"BULL_PUT_SPREAD": 1, "BULL_CALL_SPREAD": 1},
            "total_candidates": 2,
            "total_passed": 1,
            "total_rejected": 1,
        },
        "runtime_metadata": {
            "runtime_mode": "live",
            "as_of_date": "2026-03-11",
            "strict_live_mode": False,
            "degraded_live_mode": True,
            "used_mock_historical_fallback": False,
            "used_breadth_override": False,
            "used_placeholder_iv_inputs": True,
            "used_placeholder_iv_rank_inputs": True,
            "used_placeholder_iv_hv_ratio_inputs": False,
            "top_trade_candidate_symbols": ["XLE"],
            "trade_idea_symbols": ["XLE"],
            "feature_debug_by_symbol": {
                "XLE": {
                    "dataset": "EQUS.SUMMARY",
                    "schema": "ohlcv-1d",
                    "historical_row_provider": "databento",
                    "market_breadth_provider": "market_breadth_live",
                },
                "AMD": {
                    "dataset": "EQUS.SUMMARY",
                    "schema": "ohlcv-1d",
                    "historical_row_provider": "databento",
                    "market_breadth_provider": "market_breadth_live",
                },
            },
            "decision_trace_by_symbol": {
                "XLE": {"strategy_family": "BULL_PUT_SPREAD"},
                "AMD": {"strategy_family": "BULL_CALL_SPREAD"},
            },
        },
        "decisions": [
            {
                "symbol": "XLE",
                "final_passed": True,
                "market_regime": "TREND_UP",
                "directional_state": "BULLISH_CONTINUATION",
                "iv_state": "IV_RICH",
                "signal_state": "QUALIFIED",
                "strategy_type": "BULL_PUT_SPREAD",
                "final_score": 100.0,
                "min_score_required": 70.0,
                "rejection_reasons": [],
                "rationale": ["selected_strategy=BULL_PUT_SPREAD"],
                "close": 55.63,
                "dma20": 55.31,
                "dma50": 51.16,
                "atr20": 1.38,
                "adx14": 54.59,
                "iv_rank": 45.0,
                "iv_hv_ratio": 1.76,
                "market_breadth_pct_above_20dma": 58.0,
                "directional_checks": {
                    "adx14_gte_18": True,
                    "close_gt_dma20": True,
                    "dma20_gt_dma50": True,
                },
                "event_filter": {"passed": True, "reasons": []},
                "extension_filter": {"passed": True, "reasons": []},
                "liquidity_filter": {"passed": True, "reasons": []},
            },
            {
                "symbol": "AMD",
                "final_passed": False,
                "market_regime": "TREND_UP",
                "directional_state": "NEUTRAL",
                "iv_state": "IV_NORMAL",
                "signal_state": "REJECTED",
                "strategy_type": "BULL_CALL_SPREAD",
                "final_score": 0.0,
                "min_score_required": 70.0,
                "rejection_reasons": ["directional state is not actionable"],
                "rationale": ["directional state is not actionable"],
                "close": 203.67,
                "dma20": 202.38,
                "dma50": 216.50,
                "atr20": 10.15,
                "adx14": 16.29,
                "iv_rank": 45.0,
                "iv_hv_ratio": 1.09,
                "market_breadth_pct_above_20dma": 58.0,
                "directional_checks": {
                    "adx14_gte_18": False,
                    "close_gt_dma20": True,
                    "dma20_gt_dma50": False,
                },
                "event_filter": {"passed": True, "reasons": []},
                "extension_filter": {"passed": True, "reasons": []},
                "liquidity_filter": {"passed": True, "reasons": []},
            },
        ],
    }


def test_build_run_summary_row_returns_expected_fields() -> None:
    row = build_run_summary_row(_sample_payload())
    assert row["run_id"] == "scan_test_001"
    assert row["runtime_mode"] == "live"
    assert row["passed_count"] == 1
    assert row["rejected_count"] == 1
    assert row["used_placeholder_iv_rank_inputs"] is True
    assert row["used_placeholder_iv_hv_ratio_inputs"] is False


def test_build_symbol_rows_returns_expected_rows() -> None:
    rows = build_symbol_rows(_sample_payload())
    assert len(rows) == 2
    first = rows[0]
    assert first["symbol"] == "XLE"
    assert first["feature_source_dataset"] == "EQUS.SUMMARY"
    assert first["trace_strategy_family"] == "BULL_PUT_SPREAD"


def test_append_paper_live_logs_writes_jsonl_and_csv(tmp_path: Path) -> None:
    payload = _sample_payload()
    paths = default_paper_live_log_paths(str(tmp_path))

    append_paper_live_logs(payload=payload, paths=paths)

    assert paths.run_jsonl.exists()
    assert paths.symbol_jsonl.exists()
    assert paths.run_csv.exists()

    run_lines = paths.run_jsonl.read_text().strip().splitlines()
    symbol_lines = paths.symbol_jsonl.read_text().strip().splitlines()
    csv_text = paths.run_csv.read_text()

    assert len(run_lines) == 1
    assert len(symbol_lines) == 2
    assert "run_id" in csv_text
    assert "scan_test_001" in csv_text

    parsed = json.loads(run_lines[0])
    assert parsed["run_id"] == "scan_test_001"
