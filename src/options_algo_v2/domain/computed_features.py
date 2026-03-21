from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ComputedUnderlyingFeatures:
    close: float
    dma20: float
    dma50: float
    atr20: float
    adx14: float = 10.0
    rsi14: float | None = None
    five_day_return: float | None = None
    breakout_above_20d_high: bool = False
    breakdown_below_20d_low: bool = False
    breakout_volume_multiple: float = 1.0
