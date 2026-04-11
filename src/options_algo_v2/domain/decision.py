from __future__ import annotations

from dataclasses import dataclass, field

from options_algo_v2.domain.candidates import StrategyCandidate
from options_algo_v2.domain.qualification import QualificationResult


@dataclass(frozen=True)
class CandidateDecision:
    candidate: StrategyCandidate
    event_result: QualificationResult
    liquidity_result: QualificationResult
    extension_result: QualificationResult
    final_passed: bool
    final_score: float
    min_score_required: float
    underlying_price: float | None = None
    avg_daily_volume: float | None = None
    option_open_interest: int | None = None
    option_volume: int | None = None
    bid: float | None = None
    ask: float | None = None
    option_quote_age_seconds: int | None = None
    underlying_quote_age_seconds: int | None = None
    close: float | None = None
    dma20: float | None = None
    dma50: float | None = None
    atr20: float | None = None
    adx14: float | None = None
    iv_rank: float | None = None
    iv_hv_ratio: float | None = None
    market_breadth_pct_above_20dma: float | None = None
    rsi14: float | None = None
    five_day_return: float | None = None
    breakout_above_20d_high: bool | None = None
    breakdown_below_20d_low: bool | None = None
    breakout_volume_multiple: float | None = None
    extended_up: bool | None = None
    extended_down: bool | None = None
    rejection_reasons: list[str] = field(default_factory=list)
    score_breakdown: dict[str, float] = field(default_factory=dict)
