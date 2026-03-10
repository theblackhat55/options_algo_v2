import json
from pathlib import Path

import pytest

from scripts.run_nightly_scan import run_nightly_scan


def test_run_nightly_scan_returns_json_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    output_path = run_nightly_scan()
    path = Path(output_path)

    assert output_path.endswith(".json")
    assert path.exists()

    payload = json.loads(path.read_text())

    assert "summary" in payload
    assert "runtime_metadata" in payload
    assert "feature_sources" in payload
    assert payload["runtime_metadata"]["runtime_mode"] == "mock"
    assert payload["runtime_metadata"]["databento"] == {
        "dataset": "XNAS.ITCH",
        "schema": "ohlcv-1d",
        "has_api_key": "false",
    }
    assert payload["runtime_metadata"]["historical_row_provider"] == "mock"
    assert payload["runtime_metadata"]["market_breadth_provider"] == "mock"
    assert payload["runtime_metadata"]["market_breadth_provider_source"] == "mock"
    assert len(payload["feature_sources"]) == 10
    assert payload["feature_sources"][0]["historical_row_provider"] == "mock"
    assert payload["feature_sources"][0]["market_breadth_provider"] == "mock"
    assert payload["feature_sources"][0]["dataset"] == "XNAS.ITCH"
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
        (RuntimeError, NotImplementedError),
        match=(
            "live market breadth client is not implemented|"
            "databento package is not installed"
        ),
    ):
        run_nightly_scan()

