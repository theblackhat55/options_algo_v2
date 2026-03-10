from __future__ import annotations

from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.options_spread_selector import VerticalSpreadCandidate


def build_trade_candidate(
    spread: VerticalSpreadCandidate,
) -> TradeCandidate:
    short_leg = spread.short_leg
    long_leg = spread.long_leg

    width = abs(short_leg.strike - long_leg.strike)
    net_debit = max(long_leg.mid - short_leg.mid, 0.0)
    net_credit = max(short_leg.mid - long_leg.mid, 0.0)

    return TradeCandidate(
        symbol=spread.symbol,
        strategy_family=spread.strategy_family,
        expiration=short_leg.expiration,
        short_leg=short_leg,
        long_leg=long_leg,
        net_debit=net_debit,
        net_credit=net_credit,
        width=width,
    )
