from __future__ import annotations

from options_algo_v2.domain.options_chain import OptionQuote


def select_quotes_nearest_delta(
    quotes: list[OptionQuote],
    *,
    target_delta: float,
    top_n: int,
) -> list[OptionQuote]:
    return sorted(
        quotes,
        key=lambda quote: abs(abs(quote.delta or 0.0) - target_delta),
    )[:top_n]


def filter_quotes_by_delta_band(
    quotes: list[OptionQuote],
    *,
    min_abs_delta: float,
    max_abs_delta: float,
) -> list[OptionQuote]:
    selected: list[OptionQuote] = []
    for quote in quotes:
        delta = abs(quote.delta or 0.0)
        if min_abs_delta <= delta <= max_abs_delta:
            selected.append(quote)
    return selected
