from __future__ import annotations

from options_algo_v2.domain.trade_candidate import TradeCandidate


def has_positive_width(candidate: TradeCandidate) -> bool:
    return candidate.width > 0.0


def has_valid_net_debit_or_credit(candidate: TradeCandidate) -> bool:
    if candidate.net_debit < 0.0 or candidate.net_credit < 0.0:
        return False
    return candidate.net_debit > 0.0 or candidate.net_credit > 0.0


def passes_min_open_interest(
    candidate: TradeCandidate,
    *,
    min_open_interest: int,
) -> bool:
    return (
        candidate.short_leg.open_interest >= min_open_interest
        and candidate.long_leg.open_interest >= min_open_interest
    )


def passes_max_bid_ask_spread_width(
    candidate: TradeCandidate,
    *,
    max_spread_width: float,
) -> bool:
    short_spread = candidate.short_leg.ask - candidate.short_leg.bid
    long_spread = candidate.long_leg.ask - candidate.long_leg.bid
    return short_spread <= max_spread_width and long_spread <= max_spread_width
