import json
from pathlib import Path

from scripts.inspect_scan_result import inspect_scan_result


def test_inspect_scan_result_returns_zero_for_valid_file(
    tmp_path: Path,
    capsys,
) -> None:
    payload = {
        "run_id": "scan_test_001",
        "generated_at": "2026-03-10T17:36:54+00:00",
        "config_versions": {
            "universe": "universe_v1",
            "strategy": "strategy_v1",
            "risk": "risk_v1",
        },
        "runtime_metadata": {
            "runtime_mode": "mock",
            "databento": {
                "dataset": "XNAS.ITCH",
                "schema": "ohlcv-1d",
                "has_api_key": "false",
            },
        },
        "summary": {
            "total_candidates": 10,
            "total_passed": 3,
            "total_rejected": 7,
            "rejection_reason_counts": {
                "bullish setup is too extended above 20 dma": 2,
                "market regime does not permit new entries": 5,
            },
            "signal_state_counts": {
                "QUALIFIED": 5,
                "REJECTED": 5,
            },
            "strategy_type_counts": {
                "BULL_CALL_SPREAD": 5,
                "BULL_PUT_SPREAD": 5,
            },
            "passed_symbols": ["AAPL", "MSFT", "NVDA"],
            "rejected_symbols": ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "SMH"],
        },
        "decisions": [],
    }

    path = tmp_path / "scan_result.json"
    path.write_text(json.dumps(payload))

    exit_code = inspect_scan_result(str(path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run_id=scan_test_001" in captured.out
    assert "runtime_mode=mock" in captured.out
    assert "databento_runtime=" in captured.out
    assert "summary=total=10,passed=3,rejected=7" in captured.out
    assert "rejection_reason_counts=" in captured.out
    assert "signal_state_counts=" in captured.out
    assert "strategy_type_counts=" in captured.out
    assert "passed_symbols=['AAPL', 'MSFT', 'NVDA']" in captured.out


def test_inspect_scan_result_returns_one_for_missing_file(capsys) -> None:
    exit_code = inspect_scan_result("does_not_exist.json")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "error=file_not_found" in captured.out
