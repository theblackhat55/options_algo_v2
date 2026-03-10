from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.domain.market_breadth_snapshot import MarketBreadthSnapshot


@dataclass(frozen=True)
class PlaceholderLiveMarketBreadthClient:
    source: str = "live_placeholder"

    def get_market_breadth_snapshot(self) -> MarketBreadthSnapshot:
        raise NotImplementedError("live market breadth client is not implemented")
