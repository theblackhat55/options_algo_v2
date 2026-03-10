from __future__ import annotations

from collections import defaultdict

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot


def group_quotes_by_expiration(
    chain: OptionsChainSnapshot,
) -> dict[str, list[OptionQuote]]:
    grouped: dict[str, list[OptionQuote]] = defaultdict(list)
    for quote in chain.quotes:
        grouped[quote.expiration].append(quote)
    return dict(grouped)


def select_expirations_by_preference(
    chain: OptionsChainSnapshot,
    *,
    preferred_expirations: list[str],
) -> list[str]:
    grouped = group_quotes_by_expiration(chain)
    return [exp for exp in preferred_expirations if exp in grouped]
