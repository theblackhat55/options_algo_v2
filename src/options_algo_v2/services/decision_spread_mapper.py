from __future__ import annotations

from options_algo_v2.domain.decision import CandidateDecision


def get_target_spread_family(decision: CandidateDecision) -> str:
    return decision.candidate.strategy_type.value
