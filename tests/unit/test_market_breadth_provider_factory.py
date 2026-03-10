from __future__ import annotations

import pytest

from options_algo_v2.domain.market_breadth_snapshot import MarketBreadthSnapshot
from options_algo_v2.services.market_breadth_provider_factory import (
    LiveMarketBreadthProvider,
    MockMarketBreadthProvider,
    build_market_breadth_provider,
    get_market_breadth_provider_name,
    get_market_breadth_provider_source,
)


def test_build_market_breadth_provider_returns_mock_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPTIONS_ALGO_RUNTIME_MODE", raising=False)

    provider = build_market_breadth_provider()

    assert isinstance(provider, MockMarketBreadthProvider)
    assert get_market_breadth_provider_name() == "mock"
    assert get_market_breadth_provider_source() == "mock"


def test_build_market_breadth_provider_returns_live_provider_in_live_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")

    provider = build_market_breadth_provider()

    assert isinstance(provider, LiveMarketBreadthProvider)
    assert get_market_breadth_provider_name() == "market_breadth_live"
    assert get_market_breadth_provider_source() == "market_breadth_live"


def test_live_market_breadth_provider_uses_client_snapshot() -> None:
    class FakeLiveMarketBreadthClient:
        def get_market_breadth_snapshot(self) -> MarketBreadthSnapshot:
            return MarketBreadthSnapshot(
                pct_above_20dma=58.0,
                timestamp="2026-03-10T21:00:00Z",
                source="fake_live_breadth",
            )

    provider = LiveMarketBreadthProvider(client=FakeLiveMarketBreadthClient())

    assert provider.get_pct_above_20dma(symbol="AAPL") == 58.0
