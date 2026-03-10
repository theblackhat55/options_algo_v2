from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime


@dataclass(frozen=True)
class CandidateEvaluationInput:
    symbol: str
    market_regime: MarketRegime
    directional_state: DirectionalState
    iv_state: IVState
    earnings_date: date | None
    planned_latest_exit: date
    underlying_price: float
    avg_daily_volume: float
    option_open_interest: int
    option_volume: int
    bid: float
    ask: float
    option_quote_age_seconds: int
    underlying_quote_age_seconds: int
    close: float
    dma20: float
    atr20: float
    expected_move_fit: bool
