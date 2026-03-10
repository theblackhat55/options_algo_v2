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
    rejection_reasons: list[str] = field(default_factory=list)
