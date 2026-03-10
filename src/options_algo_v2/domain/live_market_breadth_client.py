from __future__ import annotations

from typing import Protocol

from options_algo_v2.domain.market_breadth_snapshot import MarketBreadthSnapshot


class LiveMarketBreadthClient(Protocol):
    def get_market_breadth_snapshot(self) -> MarketBreadthSnapshot:
        ...
