from __future__ import annotations

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.options_chain_provider import OptionsChainProvider
from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.decision_spread_selector import (
    select_spread_candidates_for_decision,
)
from options_algo_v2.services.qualified_trade_candidate_builder import (
    build_qualified_trade_candidates,
)


def build_trade_candidates_for_decision(
    *,
    decision: CandidateDecision,
    options_chain_provider: OptionsChainProvider,
    expiration: str,
    min_open_interest: int,
    max_bid_ask_spread_width: float,
) -> list[TradeCandidate]:
    chain = options_chain_provider.get_chain(symbol=decision.candidate.symbol)
    spreads = select_spread_candidates_for_decision(
        decision=decision,
        chain=chain,
        expiration=expiration,
    )
    return build_qualified_trade_candidates(
        spreads,
        min_open_interest=min_open_interest,
        max_bid_ask_spread_width=max_bid_ask_spread_width,
    )
