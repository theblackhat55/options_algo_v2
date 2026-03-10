from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComputedUnderlyingFeatures:
    close: float
    dma20: float
    dma50: float
    atr20: float
