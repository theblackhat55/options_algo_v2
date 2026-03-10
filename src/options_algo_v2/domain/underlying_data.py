from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnderlyingSnapshot:
    symbol: str
    close: float
    volume: float
    timestamp: str
