import pytest

from options_algo_v2.services.historical_row_provider_factory import (
    DatabentoHistoricalRowProvider,
    MockHistoricalRowProvider,
    build_historical_row_provider,
)


def test_build_historical_row_provider_returns_mock_in_default_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPTIONS_ALGO_RUNTIME_MODE", raising=False)

    provider = build_historical_row_provider()

    assert isinstance(provider, MockHistoricalRowProvider)
    rows = provider.get_bar_rows(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )
    assert len(rows) == 50


def test_build_historical_row_provider_returns_mock_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    provider = build_historical_row_provider()

    assert isinstance(provider, MockHistoricalRowProvider)
    rows = provider.get_bar_rows(
        symbol="MSFT",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )
    assert len(rows) == 50


def test_build_historical_row_provider_raises_in_live_mode_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DATABENTO_API_KEY"):
        build_historical_row_provider()


def test_build_historical_row_provider_returns_live_provider_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")

    provider = build_historical_row_provider()

    assert isinstance(provider, DatabentoHistoricalRowProvider)
