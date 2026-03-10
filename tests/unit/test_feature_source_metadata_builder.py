import pytest

from options_algo_v2.services.feature_source_metadata_builder import (
    build_feature_source_metadata,
)


def test_build_feature_source_metadata_returns_mock_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")
    monkeypatch.delenv("DATABENTO_DATASET", raising=False)
    monkeypatch.delenv("DATABENTO_SCHEMA", raising=False)

    metadata = build_feature_source_metadata(symbol="AAPL")

    assert metadata.symbol == "AAPL"
    assert metadata.historical_row_provider == "mock"
    assert metadata.market_breadth_provider == "mock"
    assert metadata.dataset == "XNAS.ITCH"
    assert metadata.schema == "ohlcv-1d"


def test_build_feature_source_metadata_returns_live_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.setenv("DATABENTO_DATASET", "GLBX.MDP3")
    monkeypatch.setenv("DATABENTO_SCHEMA", "ohlcv-1m")

    metadata = build_feature_source_metadata(symbol="SPY")

    assert metadata.symbol == "SPY"
    assert metadata.historical_row_provider == "live_placeholder"
    assert metadata.market_breadth_provider == "live_placeholder"
    assert metadata.dataset == "GLBX.MDP3"
    assert metadata.schema == "ohlcv-1m"
