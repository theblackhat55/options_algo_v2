from __future__ import annotations

from datetime import date

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.decision_spread_mapper import get_target_spread_family
from options_algo_v2.services.options_delta_selector import (
    filter_quotes_by_delta_band,
)
from options_algo_v2.services.options_dte_selector import (
    rank_expirations_by_target_dte_distance,
    select_expirations_in_dte_window,
)
from options_algo_v2.services.options_expiration_selector import (
    group_quotes_by_expiration,
)
from options_algo_v2.services.options_spread_selector import (
    VerticalSpreadCandidate,
    select_vertical_call_spread_candidates,
    select_vertical_put_spread_candidates,
)
from options_algo_v2.services.runtime_execution_settings import (
    get_runtime_execution_settings,
)


def select_spread_candidates_across_expirations(
    *,
    decision: CandidateDecision,
    chain: OptionsChainSnapshot,
    as_of_date: date,
    min_dte: int = 25,
    max_dte: int = 45,
    target_dte: int = 35,
    credit_short_delta_min: float = 0.15,
    credit_short_delta_max: float = 0.30,
    debit_long_delta_min: float = 0.45,
    debit_long_delta_max: float = 0.65,
) -> list[VerticalSpreadCandidate]:
    grouped = group_quotes_by_expiration(chain)
    expirations = list(grouped.keys())

    eligible_expirations = select_expirations_in_dte_window(
        expirations,
        as_of_date=as_of_date,
        min_dte=min_dte,
        max_dte=max_dte,
    )
    ranked_expirations = rank_expirations_by_target_dte_distance(
        eligible_expirations,
        as_of_date=as_of_date,
        target_dte=target_dte,
    )

    strategy_family = get_target_spread_family(decision)
    selected_candidates: list[VerticalSpreadCandidate] = []

    for expiration in ranked_expirations:
        quotes = grouped[expiration]

        filtered_quotes = _filter_quotes_for_strategy(
            strategy_family=strategy_family,
            quotes=quotes,
            credit_short_delta_min=credit_short_delta_min,
            credit_short_delta_max=credit_short_delta_max,
            debit_long_delta_min=debit_long_delta_min,
            debit_long_delta_max=debit_long_delta_max,
        )

        filtered_chain = OptionsChainSnapshot(
            symbol=chain.symbol,
            quotes=filtered_quotes,
            as_of=chain.as_of,
            source=chain.source,
        )

        if strategy_family == "BULL_CALL_SPREAD":
            selected_candidates.extend(
                select_vertical_call_spread_candidates(
                    chain=filtered_chain,
                    expiration=expiration,
                )
            )
        elif strategy_family == "BULL_PUT_SPREAD":
            selected_candidates.extend(
                select_vertical_put_spread_candidates(
                    chain=filtered_chain,
                    expiration=expiration,
                )
            )

    return selected_candidates


def _filter_quotes_for_strategy(
    *,
    strategy_family: str,
    quotes: list[OptionQuote],
    credit_short_delta_min: float = 0.15,
    credit_short_delta_max: float = 0.30,
    debit_long_delta_min: float = 0.45,
    debit_long_delta_max: float = 0.65,
) -> list[OptionQuote]:
    execution_settings = get_runtime_execution_settings()

    if strategy_family == "BULL_CALL_SPREAD":
        calls = [
            quote for quote in quotes if str(quote.option_type).lower() == "call"
        ]
        filtered = filter_quotes_by_delta_band(
            calls,
            min_abs_delta=debit_long_delta_min,
            max_abs_delta=debit_long_delta_max,
        )
        if filtered:
            return filtered
        if execution_settings.allow_relaxed_liquidity_thresholds:
            return calls
        return []

    if strategy_family == "BULL_PUT_SPREAD":
        puts = [
            quote for quote in quotes if str(quote.option_type).lower() == "put"
        ]
        filtered = filter_quotes_by_delta_band(
            puts,
            min_abs_delta=credit_short_delta_min,
            max_abs_delta=credit_short_delta_max,
        )
        if filtered:
            return filtered
        if execution_settings.allow_relaxed_liquidity_thresholds:
            return puts
        return []

    return []
