from __future__ import annotations

from datetime import date

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.services.best_trade_candidate_selector import (
    select_best_trade_candidate_per_symbol,
)
from options_algo_v2.services.options_chain_provider_factory import (
    build_options_chain_provider,
)
from options_algo_v2.services.runtime_execution_settings import (
    get_runtime_execution_settings,
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
    as_of_date: date | None = None,
) -> list[dict[str, object]]:
    resolved_as_of_date = (
        as_of_date or get_runtime_execution_settings().as_of_date
    )
    options_chain_provider = build_options_chain_provider()

    serialized_candidates: list[dict[str, object]] = []
    for decision in decisions:
        if not decision.final_passed:
            continue

        trade_candidates = build_trade_candidates_for_decision(
            decision=decision,
            options_chain_provider=options_chain_provider,
            expiration=expiration,
            min_open_interest=min_open_interest,
            max_bid_ask_spread_width=max_bid_ask_spread_width,
            as_of_date=resolved_as_of_date,
        )
        serialized_candidates.extend(
            serialize_trade_candidate(candidate) for candidate in trade_candidates
        )

    return select_best_trade_candidate_per_symbol(serialized_candidates)
