from __future__ import annotations

import pytest

from options_algo_v2.services.historical_row_provider_factory import (
    DatabentoHistoricalRowProvider,
    MockHistoricalRowProvider,
    build_historical_row_provider,
    get_historical_row_provider_name,
    get_historical_row_provider_source,
)


def test_build_historical_row_provider_returns_mock_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPTIONS_ALGO_RUNTIME_MODE", raising=False)

    provider = build_historical_row_provider()

    assert isinstance(provider, MockHistoricalRowProvider)
    assert get_historical_row_provider_name() == "mock"
    assert get_historical_row_provider_source() == "mock"


def test_build_historical_row_provider_returns_mock_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    provider = build_historical_row_provider()

    assert isinstance(provider, MockHistoricalRowProvider)


def test_build_historical_row_provider_live_mode_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    with pytest.raises(
        ValueError,
        match="DATABENTO_API_KEY is required for live runtime mode",
    ):
        build_historical_row_provider()


def test_build_historical_row_provider_returns_databento_provider_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")

    provider = build_historical_row_provider()

    assert isinstance(provider, DatabentoHistoricalRowProvider)
    assert get_historical_row_provider_name() == "databento"
    assert get_historical_row_provider_source() == "databento"
