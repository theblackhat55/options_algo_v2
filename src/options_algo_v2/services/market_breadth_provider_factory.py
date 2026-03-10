from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.domain.market_breadth_provider import MarketBreadthProvider
from options_algo_v2.services.runtime_mode import get_runtime_mode


@dataclass(frozen=True)
class MockMarketBreadthProvider:
    def get_pct_above_20dma(self, *, symbol: str) -> float:
        bullish_symbols = {"AAPL", "MSFT", "NVDA", "SPY", "QQQ"}
        if symbol in bullish_symbols:
            return 62.0
        return 48.0


@dataclass(frozen=True)
class LiveMarketBreadthProvider:
    def get_pct_above_20dma(self, *, symbol: str) -> float:
        del symbol
        raise NotImplementedError("live market breadth provider is not implemented")


def build_market_breadth_provider() -> MarketBreadthProvider:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        return LiveMarketBreadthProvider()

    return MockMarketBreadthProvider()


def get_market_breadth_provider_name() -> str:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        return "live_placeholder"

    return "mock"
