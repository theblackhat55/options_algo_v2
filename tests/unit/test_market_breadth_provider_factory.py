import pytest

from options_algo_v2.domain.market_breadth_snapshot import MarketBreadthSnapshot
from options_algo_v2.services.market_breadth_provider_factory import (
    LiveMarketBreadthProvider,
    MockMarketBreadthProvider,
    build_market_breadth_provider,
    get_market_breadth_provider_name,
    get_market_breadth_provider_source,
)


class FakeLiveMarketBreadthClient:
    def get_market_breadth_snapshot(self) -> MarketBreadthSnapshot:
        return MarketBreadthSnapshot(
            pct_above_20dma=57.5,
            timestamp="2026-03-10T21:00:00Z",
            source="fake_live_source",
        )


def test_build_market_breadth_provider_returns_mock_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPTIONS_ALGO_RUNTIME_MODE", raising=False)

    provider = build_market_breadth_provider()

    assert isinstance(provider, MockMarketBreadthProvider)
    assert provider.get_pct_above_20dma(symbol="AAPL") == 62.0
    assert provider.get_pct_above_20dma(symbol="XLF") == 48.0
    assert get_market_breadth_provider_name() == "mock"
    assert get_market_breadth_provider_source() == "mock"


def test_build_market_breadth_provider_returns_mock_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    provider = build_market_breadth_provider()

    assert isinstance(provider, MockMarketBreadthProvider)
    assert provider.get_pct_above_20dma(symbol="NVDA") == 62.0
    assert provider.get_pct_above_20dma(symbol="IWM") == 48.0


def test_build_market_breadth_provider_returns_live_in_live_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")

    provider = build_market_breadth_provider()

    assert isinstance(provider, LiveMarketBreadthProvider)
    assert get_market_breadth_provider_name() == "live"
    assert get_market_breadth_provider_source() == "live_placeholder"

    with pytest.raises(
        NotImplementedError,
        match="live market breadth client is not implemented",
    ):
        provider.get_pct_above_20dma(symbol="SPY")


def test_live_market_breadth_provider_uses_client_snapshot() -> None:
    provider = LiveMarketBreadthProvider(client=FakeLiveMarketBreadthClient())

    assert provider.get_pct_above_20dma(symbol="SPY") == 57.5
