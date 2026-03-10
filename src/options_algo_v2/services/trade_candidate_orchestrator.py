from __future__ import annotations

from datetime import date

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.options_chain_provider import OptionsChainProvider
from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.expiration_aware_spread_selector import (
    select_spread_candidates_across_expirations,
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
    _ = expiration
    chain = options_chain_provider.get_chain(symbol=decision.candidate.symbol)
    as_of = date(2026, 3, 10)

    spread_candidates = select_spread_candidates_across_expirations(
        decision=decision,
        chain=chain,
        as_of_date=as_of,
        min_dte=30,
        max_dte=60,
        target_dte=38,
    )

    if not spread_candidates:
        spread_candidates = select_spread_candidates_across_expirations(
            decision=decision,
            chain=chain,
            as_of_date=as_of,
            min_dte=1,
            max_dte=14,
            target_dte=7,
        )

    return build_qualified_trade_candidates(
        spread_candidates,
        min_open_interest=min_open_interest,
        max_bid_ask_spread_width=max_bid_ask_spread_width,
    )
