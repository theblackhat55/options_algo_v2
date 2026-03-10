from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketBreadthSnapshot:
    pct_above_20dma: float
    timestamp: str
    source: str
