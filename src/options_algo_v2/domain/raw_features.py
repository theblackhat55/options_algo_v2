from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RawFeatureInput:
    symbol: str
    close: float
    dma20: float
    dma50: float
    atr20: float
    adx14: float
    iv_rank: float
    iv_hv_ratio: float
    avg_daily_volume: float
    option_open_interest: int
    option_volume: int
    bid: float
    ask: float
    option_quote_age_seconds: int
    underlying_quote_age_seconds: int
    market_breadth_pct_above_20dma: float
    earnings_date: date | None
    entry_date: date
    dte_days: int
