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
    close: float | None = None
    dma20: float | None = None
    dma50: float | None = None
    atr20: float | None = None
    adx14: float | None = None
    iv_rank: float | None = None
    iv_hv_ratio: float | None = None
    market_breadth_pct_above_20dma: float | None = None
    rejection_reasons: list[str] = field(default_factory=list)
