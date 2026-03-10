from __future__ import annotations

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.services.options_chain_provider_factory import (
    build_options_chain_provider,
)
from options_algo_v2.services.trade_candidate_orchestrator import (
    build_trade_candidates_for_decision,
)
from options_algo_v2.services.trade_candidate_serializer import (
    serialize_trade_candidate,
)


def build_serialized_trade_candidates(
    *,
    decisions: list[CandidateDecision],
    expiration: str,
    min_open_interest: int,
    max_bid_ask_spread_width: float,
) -> list[dict[str, object]]:
    provider = build_options_chain_provider()
    serialized_candidates: list[dict[str, object]] = []

    for decision in decisions:
        if not decision.final_passed:
            continue

        candidates = build_trade_candidates_for_decision(
            decision=decision,
            options_chain_provider=provider,
            expiration=expiration,
            min_open_interest=min_open_interest,
            max_bid_ask_spread_width=max_bid_ask_spread_width,
        )

        serialized_candidates.extend(
            serialize_trade_candidate(candidate) for candidate in candidates
        )

    return serialized_candidates
