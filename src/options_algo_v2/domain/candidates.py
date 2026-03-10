from __future__ import annotations

from dataclasses import dataclass, field

from options_algo_v2.domain.enums import (
    DirectionalState,
    IVState,
    MarketRegime,
    SignalState,
    StrategyType,
)


@dataclass(frozen=True)
class StrategyCandidate:
    symbol: str
    market_regime: MarketRegime
    directional_state: DirectionalState
    iv_state: IVState
    strategy_type: StrategyType
    signal_state: SignalState
    score: float = 0.0
    rationale: list[str] = field(default_factory=list)
