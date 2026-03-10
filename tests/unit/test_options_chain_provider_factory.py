import pytest

from options_algo_v2.services.options_chain_provider_factory import (
    LiveOptionsChainProvider,
    MockOptionsChainProvider,
    build_options_chain_provider,
    get_options_chain_provider_name,
    get_options_chain_provider_source,
)


def test_build_options_chain_provider_returns_mock_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPTIONS_ALGO_RUNTIME_MODE", raising=False)

    provider = build_options_chain_provider()

    assert isinstance(provider, MockOptionsChainProvider)
    snapshot = provider.get_chain(symbol="AAPL")
    assert snapshot.symbol == "AAPL"
    assert snapshot.source == "mock"
    assert len(snapshot.quotes) == 4
    assert get_options_chain_provider_name() == "mock"
    assert get_options_chain_provider_source() == "mock"


def test_build_options_chain_provider_returns_mock_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    provider = build_options_chain_provider()

    assert isinstance(provider, MockOptionsChainProvider)
    snapshot = provider.get_chain(symbol="MSFT")
    assert snapshot.symbol == "MSFT"
    assert len(snapshot.quotes) == 4


def test_build_options_chain_provider_returns_live_in_live_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")

    provider = build_options_chain_provider()

    assert isinstance(provider, LiveOptionsChainProvider)
    assert get_options_chain_provider_name() == "live"
    assert get_options_chain_provider_source() == "live_options_placeholder"

    with pytest.raises(
        NotImplementedError,
        match="live options chain client is not implemented",
    ):
        provider.get_chain(symbol="SPY")
