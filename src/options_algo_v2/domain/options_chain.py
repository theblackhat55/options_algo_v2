from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OptionQuote:
    symbol: str
    option_symbol: str
    expiration: str
    strike: float
    option_type: str
    bid: float
    ask: float
    mid: float
    delta: float | None
    implied_volatility: float | None = None
    open_interest: int = 0
    volume: int = 0


@dataclass(frozen=True)
class OptionsChainSnapshot:
    symbol: str
    quotes: list[OptionQuote] = field(default_factory=list)
    as_of: str = ""
    source: str = ""
