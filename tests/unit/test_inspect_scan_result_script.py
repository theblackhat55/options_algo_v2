import json
from pathlib import Path

from scripts.inspect_scan_result import inspect_scan_result


def test_inspect_scan_result_returns_zero_for_valid_file(tmp_path: Path, capsys) -> None:
    payload = {
        "run_id": "scan_test_001",
        "generated_at": "2026-03-10T18:00:00+00:00",
        "config_versions": {
            "risk": "risk_v1",
            "strategy": "strategy_v1",
            "universe": "universe_v1",
        },
        "runtime_metadata": {
            "runtime_mode": "mock",
            "historical_row_provider": "mock",
            "market_breadth_provider": "mock",
            "market_breadth_provider_source": "mock",
            "databento": {
                "dataset": "XNAS.ITCH",
                "schema": "ohlcv-1d",
                "has_api_key": "false",
            },
        },
        "feature_sources": [
            {
                "symbol": "AAPL",
                "historical_row_provider": "mock",
                "market_breadth_provider": "mock",
                "dataset": "XNAS.ITCH",
                "schema": "ohlcv-1d",
            },
            {
                "symbol": "MSFT",
                "historical_row_provider": "mock",
                "market_breadth_provider": "mock",
                "dataset": "XNAS.ITCH",
                "schema": "ohlcv-1d",
            },
        ],
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
    }

    artifact = tmp_path / "scan_result.json"
    artifact.write_text(json.dumps(payload))

    exit_code = inspect_scan_result(str(artifact))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "run_id=scan_test_001" in captured.out
    assert "runtime_mode=mock" in captured.out
    assert "historical_row_provider=mock" in captured.out
    assert "market_breadth_provider=mock" in captured.out
    assert "market_breadth_provider_source=mock" in captured.out
    assert (
        "databento_runtime={'dataset': 'XNAS.ITCH', 'schema': 'ohlcv-1d', "
        "'has_api_key': 'false'}"
    ) in captured.out
    assert (
        "feature_sources=[{'symbol': 'AAPL', 'historical_row_provider': 'mock', "
        "'market_breadth_provider': 'mock', 'dataset': 'XNAS.ITCH', "
        "'schema': 'ohlcv-1d'}, {'symbol': 'MSFT', 'historical_row_provider': "
        "'mock', 'market_breadth_provider': 'mock', 'dataset': 'XNAS.ITCH', "
        "'schema': 'ohlcv-1d'}]"
    ) in captured.out
    assert (
        "feature_source_counts_by_historical_row_provider={'mock': 2}"
    ) in captured.out
    assert (
        "feature_source_counts_by_market_breadth_provider={'mock': 2}"
    ) in captured.out
    assert (
        "feature_source_counts_by_dataset_schema={'XNAS.ITCH|ohlcv-1d': 2}"
    ) in captured.out
    assert "summary=total=10,passed=3,rejected=7" in captured.out


def test_inspect_scan_result_returns_one_for_missing_file(capsys) -> None:
    exit_code = inspect_scan_result("missing_scan_result.json")
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "error=file_not_found" in captured.out
