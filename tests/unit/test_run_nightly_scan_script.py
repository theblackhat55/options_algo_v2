import json
from pathlib import Path

import pytest

from scripts.run_nightly_scan import run_nightly_scan


def test_run_nightly_scan_returns_json_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    output_path = run_nightly_scan()
    path = Path(output_path)

    assert output_path.endswith(".json")
    assert path.exists()

    payload = json.loads(path.read_text())

    assert "summary" in payload
    assert "runtime_metadata" in payload
    assert "feature_sources" in payload
    assert "trade_ideas" in payload
    assert payload["runtime_metadata"]["runtime_mode"] == "mock"
    databento = payload["runtime_metadata"]["databento"]
    assert isinstance(databento, dict)
    assert databento["schema"] == "ohlcv-1d"
    assert databento["has_api_key"] == "false"
    assert isinstance(databento["dataset"], str)
    assert databento["dataset"]
    assert payload["runtime_metadata"]["historical_row_provider"] == "mock"
    assert payload["runtime_metadata"]["historical_row_provider_source"] == "mock"
    assert payload["runtime_metadata"]["market_breadth_provider"] == "mock"
    assert payload["runtime_metadata"]["market_breadth_provider_source"] == "mock"
    assert payload["runtime_metadata"][
        "feature_source_counts_by_historical_row_provider"
    ] == {"mock": 10}
    assert payload["runtime_metadata"][
        "feature_source_counts_by_market_breadth_provider"
    ] == {"mock": 10}
    dataset_schema_counts = payload["runtime_metadata"][
        "feature_source_counts_by_dataset_schema"
    ]
    assert isinstance(dataset_schema_counts, dict)
    assert len(dataset_schema_counts) == 1
    ((dataset_schema_key, dataset_schema_count),) = dataset_schema_counts.items()
    assert dataset_schema_key.endswith("|ohlcv-1d")
    assert dataset_schema_count == 10
    assert payload["runtime_metadata"]["trade_candidate_counts_by_strategy_family"] == {
        "BULL_PUT_SPREAD": 3
    }
    assert payload["runtime_metadata"]["trade_candidate_counts_by_symbol"] == {
        "AAPL": 1,
        "MSFT": 1,
        "NVDA": 1,
    }
    assert payload["runtime_metadata"]["ranked_trade_candidate_counts_by_strategy_family"] == {
        "BULL_PUT_SPREAD": 3
    }
    assert payload["runtime_metadata"]["ranked_trade_candidate_symbols"] == [
        "AAPL",
        "MSFT",
        "NVDA",
    ]
    assert payload["runtime_metadata"]["top_trade_candidate_symbols"] == [
        "AAPL",
        "MSFT",
        "NVDA",
    ]
    assert payload["runtime_metadata"]["trade_idea_count"] == 3
    assert payload["runtime_metadata"]["trade_idea_symbols"] == [
        "AAPL",
        "MSFT",
        "NVDA",
    ]
    assert payload["runtime_metadata"]["trade_idea_counts_by_strategy_family"] == {
        "BULL_PUT_SPREAD": 3
    }
    assert len(payload["runtime_metadata"]["top_trade_summary_rows"]) == 3
    assert payload["runtime_metadata"]["top_trade_summary_rows"][0]["symbol"] == "AAPL"
    assert "trade_candidates" in payload
    assert len(payload["trade_candidates"]) == 3
    assert len(payload["trade_ideas"]) == 3
    assert payload["trade_ideas"][0]["strategy_family"] == "BULL_PUT_SPREAD"
    assert len(payload["feature_sources"]) == 10
    assert payload["feature_sources"][0]["historical_row_provider"] == "mock"
    assert payload["feature_sources"][0]["market_breadth_provider"] == "mock"
    assert isinstance(payload["feature_sources"][0]["dataset"], str)
    assert payload["feature_sources"][0]["dataset"]
    assert payload["feature_sources"][0]["schema"] == "ohlcv-1d"
    assert "rejection_reason_counts" in payload["summary"]
    assert "signal_state_counts" in payload["summary"]
    assert "strategy_type_counts" in payload["summary"]


def test_run_nightly_scan_live_mode_requires_databento_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DATABENTO_API_KEY"):
        run_nightly_scan()


def test_run_nightly_scan_live_mode_with_key_requires_live_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")

    with pytest.raises(
        (RuntimeError, NotImplementedError, ValueError, Exception),
        match=(
            "live market breadth data source is not configured|"
            "databento package is not installed|"
            "POLYGON_API_KEY is required for live options chain mode|"
            "auth_authentication_failed|"
            "Authentication failed"
        ),
    ):
        run_nightly_scan()

