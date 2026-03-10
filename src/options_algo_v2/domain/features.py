from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketRegimeFeatures:
    spy_close_above_20dma: bool
    spy_20dma_above_50dma: bool
    spy_close_below_20dma: bool
    spy_20dma_below_50dma: bool
    breadth_pct_above_20dma: float
    vix_defensive: bool = False


@dataclass(frozen=True)
class IVFeatures:
    iv_rank: float | None
    iv_hv_ratio: float | None
    iv_rv_spread: float | None


@dataclass(frozen=True)
class DirectionalFeatures:
    close_above_20dma: bool
    close_above_50dma: bool
    close_below_20dma: bool
    close_below_50dma: bool
    adx: float
    rsi: float
    five_day_return: float
    breakout_above_20d_high: bool
    breakdown_below_20d_low: bool
    breakout_volume_multiple: float
    extended_up: bool
    extended_down: bool
