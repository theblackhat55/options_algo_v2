from __future__ import annotations

from typing import Protocol


class MarketBreadthProvider(Protocol):
    def get_pct_above_20dma(self, *, symbol: str) -> float:
        ...
