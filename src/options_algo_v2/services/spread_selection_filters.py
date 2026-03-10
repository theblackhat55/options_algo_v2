from __future__ import annotations

from options_algo_v2.domain.trade_candidate import TradeCandidate


def passes_bull_call_delta_filter(candidate: TradeCandidate) -> bool:
    delta = candidate.long_leg.delta
    if delta is None:
        return False
    return 0.30 <= delta <= 0.45


def passes_bull_put_delta_filter(candidate: TradeCandidate) -> bool:
    delta = candidate.short_leg.delta
    if delta is None:
        return False
    return 0.20 <= abs(delta) <= 0.35


def passes_debit_width_filter(candidate: TradeCandidate) -> bool:
    if candidate.strategy_family != "BULL_CALL_SPREAD":
        return True
    if candidate.width <= 0:
        return False
    return candidate.net_debit <= (0.60 * candidate.width)


def passes_credit_width_filter(candidate: TradeCandidate) -> bool:
    if candidate.strategy_family != "BULL_PUT_SPREAD":
        return True
    if candidate.width <= 0:
        return False
    return candidate.net_credit >= (0.15 * candidate.width)
