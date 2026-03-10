from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OptionSnapshot:
    underlying_symbol: str
    option_symbol: str
    strike: float
    right: str
    expiry: str
    bid: float
    ask: float
    iv: float
    delta: float
    open_interest: int
    volume: int
    quote_timestamp: str
