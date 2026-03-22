from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot


@dataclass(frozen=True)
class VerticalSpreadCandidate:
    symbol: str
    strategy_family: str
    short_leg: OptionQuote
    long_leg: OptionQuote


def select_vertical_call_spread_candidates(
    *,
    chain: OptionsChainSnapshot,
    expiration: str,
) -> list[VerticalSpreadCandidate]:
    calls = [
        quote
        for quote in chain.quotes
        if str(quote.option_type).lower() == "call" and quote.expiration == expiration
    ]
    calls = sorted(calls, key=lambda quote: quote.strike)

    candidates: list[VerticalSpreadCandidate] = []
    for lower_strike_call, higher_strike_call in zip(calls, calls[1:], strict=False):
        candidates.append(
            VerticalSpreadCandidate(
                symbol=chain.symbol,
                strategy_family="BULL_CALL_SPREAD",
                short_leg=higher_strike_call,
                long_leg=lower_strike_call,
            )
        )
    return candidates


def select_vertical_put_spread_candidates(
    *,
    chain: OptionsChainSnapshot,
    expiration: str,
) -> list[VerticalSpreadCandidate]:
    puts = [
        quote
        for quote in chain.quotes
        if str(quote.option_type).lower() == "put" and quote.expiration == expiration
    ]
    puts = sorted(puts, key=lambda quote: quote.strike, reverse=True)

    candidates: list[VerticalSpreadCandidate] = []
    for left, right in zip(puts, puts[1:], strict=False):
        candidates.append(
            VerticalSpreadCandidate(
                symbol=chain.symbol,
                strategy_family="BULL_PUT_SPREAD",
                short_leg=left,
                long_leg=right,
            )
        )
    return candidates


def select_vertical_bear_call_spread_candidates(
    *,
    chain: OptionsChainSnapshot,
    expiration: str,
) -> list[VerticalSpreadCandidate]:
    calls = [
        quote
        for quote in chain.quotes
        if str(quote.option_type).lower() == "call" and quote.expiration == expiration
    ]
    calls = sorted(calls, key=lambda quote: quote.strike)

    candidates: list[VerticalSpreadCandidate] = []
    for lower_strike_call, higher_strike_call in zip(calls, calls[1:], strict=False):
        candidates.append(
            VerticalSpreadCandidate(
                symbol=chain.symbol,
                strategy_family="BEAR_CALL_SPREAD",
                short_leg=lower_strike_call,
                long_leg=higher_strike_call,
            )
        )
    return candidates


def select_vertical_bear_put_spread_candidates(
    *,
    chain: OptionsChainSnapshot,
    expiration: str,
) -> list[VerticalSpreadCandidate]:
    puts = [
        quote
        for quote in chain.quotes
        if str(quote.option_type).lower() == "put" and quote.expiration == expiration
    ]
    puts = sorted(puts, key=lambda quote: quote.strike, reverse=True)

    candidates: list[VerticalSpreadCandidate] = []
    for higher_strike_put, lower_strike_put in zip(puts, puts[1:], strict=False):
        candidates.append(
            VerticalSpreadCandidate(
                symbol=chain.symbol,
                strategy_family="BEAR_PUT_SPREAD",
                short_leg=lower_strike_put,
                long_leg=higher_strike_put,
            )
        )
    return candidates
