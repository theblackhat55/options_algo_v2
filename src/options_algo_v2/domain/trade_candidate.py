from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.domain.options_chain import OptionQuote


@dataclass(frozen=True)
class TradeCandidate:
    symbol: str
    strategy_family: str
    expiration: str
    short_leg: OptionQuote
    long_leg: OptionQuote
    net_debit: float
    net_credit: float
    width: float
