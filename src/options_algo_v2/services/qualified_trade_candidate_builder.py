from __future__ import annotations

from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.options_spread_selector import VerticalSpreadCandidate
from options_algo_v2.services.spread_quality_filters import (
    has_positive_width,
    has_valid_net_debit_or_credit,
    passes_max_bid_ask_spread_width,
    passes_min_open_interest,
)
from options_algo_v2.services.trade_candidate_builder import build_trade_candidate


def build_qualified_trade_candidates(
    spreads: list[VerticalSpreadCandidate],
    *,
    min_open_interest: int,
    max_bid_ask_spread_width: float,
) -> list[TradeCandidate]:
    candidates: list[TradeCandidate] = []

    for spread in spreads:
        candidate = build_trade_candidate(spread)

        if not has_positive_width(candidate):
            continue
        if not has_valid_net_debit_or_credit(candidate):
            continue
        if not passes_min_open_interest(
            candidate,
            min_open_interest=min_open_interest,
        ):
            continue
        if not passes_max_bid_ask_spread_width(
            candidate,
            max_spread_width=max_bid_ask_spread_width,
        ):
            continue

        candidates.append(candidate)

    return candidates
