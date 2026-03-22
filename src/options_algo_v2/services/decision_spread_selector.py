from __future__ import annotations

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.options_chain import OptionsChainSnapshot
from options_algo_v2.services.decision_spread_mapper import get_target_spread_family
from options_algo_v2.services.options_spread_selector import (
    VerticalSpreadCandidate,
    select_vertical_bear_call_spread_candidates,
    select_vertical_bear_put_spread_candidates,
    select_vertical_call_spread_candidates,
    select_vertical_put_spread_candidates,
)


def select_spread_candidates_for_decision(
    *,
    decision: CandidateDecision,
    chain: OptionsChainSnapshot,
    expiration: str,
) -> list[VerticalSpreadCandidate]:
    strategy_family = get_target_spread_family(decision)

    if strategy_family == "BULL_CALL_SPREAD":
        return select_vertical_call_spread_candidates(
            chain=chain,
            expiration=expiration,
        )

    if strategy_family == "BULL_PUT_SPREAD":
        return select_vertical_put_spread_candidates(
            chain=chain,
            expiration=expiration,
        )

    if strategy_family == "BEAR_CALL_SPREAD":
        return select_vertical_bear_call_spread_candidates(
            chain=chain,
            expiration=expiration,
        )

    if strategy_family == "BEAR_PUT_SPREAD":
        return select_vertical_bear_put_spread_candidates(
            chain=chain,
            expiration=expiration,
        )

    return []
