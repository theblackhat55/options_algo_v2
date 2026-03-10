from __future__ import annotations

from options_algo_v2.domain.decision import CandidateDecision


def serialize_candidate_decision(
    decision: CandidateDecision,
) -> dict[str, object]:
    return {
        "symbol": decision.candidate.symbol,
        "market_regime": decision.candidate.market_regime.value,
        "directional_state": decision.candidate.directional_state.value,
        "iv_state": decision.candidate.iv_state.value,
        "strategy_type": decision.candidate.strategy_type.value,
        "signal_state": decision.candidate.signal_state.value,
        "final_passed": decision.final_passed,
        "final_score": decision.final_score,
        "min_score_required": decision.min_score_required,
        "rejection_reasons": list(decision.rejection_reasons),
        "rationale": list(decision.candidate.rationale),
        "event_filter": {
            "passed": decision.event_result.passed,
            "reasons": list(decision.event_result.reasons),
        },
        "liquidity_filter": {
            "passed": decision.liquidity_result.passed,
            "reasons": list(decision.liquidity_result.reasons),
        },
        "extension_filter": {
            "passed": decision.extension_result.passed,
            "reasons": list(decision.extension_result.reasons),
        },
    }
