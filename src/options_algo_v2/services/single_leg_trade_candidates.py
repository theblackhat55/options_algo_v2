from __future__ import annotations

from datetime import date

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.enums import StrategyType
from options_algo_v2.domain.options_chain import OptionsChainSnapshot
from options_algo_v2.services.options_dte_selector import (
    rank_expirations_by_target_dte_distance,
    select_expirations_in_dte_window,
)
from options_algo_v2.services.options_expiration_selector import (
    group_quotes_by_expiration,
)
from options_algo_v2.services.single_leg_scoring import (
    score_long_call,
    score_long_put,
)
from options_algo_v2.services.single_leg_selector import (
    select_long_call_contract,
    select_long_put_contract,
)


def select_single_leg_trade_candidates(
    *,
    decision: CandidateDecision,
    chain: OptionsChainSnapshot,
    as_of_date: date,
    min_dte: int = 14,
    max_dte: int = 45,
    target_dte: int = 28,
) -> list[dict[str, object]]:
    strategy_type = decision.candidate.strategy_type

    if strategy_type not in {StrategyType.LONG_CALL, StrategyType.LONG_PUT}:
        return []

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

    candidates: list[dict[str, object]] = []

    for expiration in ranked_expirations:
        quotes = grouped[expiration]

        if strategy_type == StrategyType.LONG_CALL:
            selected = select_long_call_contract(
                [quote_to_dict(q) for q in quotes]
            )
            if not selected:
                continue

            score = score_long_call(
                expected_move_1d_pct=4.0 if "long_call_alternative_eligible" in decision.candidate.rationale else 1.0,
                iv_rank=decision.iv_rank,
                iv_hv_ratio=decision.iv_hv_ratio,
                premium=selected.get("ask"),
                delta=selected.get("delta"),
                liquidity_score=10.0,
            )

            candidates.append(
                {
                    "symbol": chain.symbol,
                    "strategy_family": StrategyType.LONG_CALL.value,
                    "expiration": str(expiration),
                    "option_type": "CALL",
                    "strike": selected.get("strike"),
                    "delta": selected.get("delta"),
                    "bid": selected.get("bid"),
                    "ask": selected.get("ask"),
                    "premium": selected.get("ask"),
                    "score": score,
                }
            )

        elif strategy_type == StrategyType.LONG_PUT:
            selected = select_long_put_contract(
                [quote_to_dict(q) for q in quotes]
            )
            if not selected:
                continue

            score = score_long_put(
                expected_move_1d_pct=4.0 if "long_put_alternative_eligible" in decision.candidate.rationale else 1.0,
                iv_rank=decision.iv_rank,
                iv_hv_ratio=decision.iv_hv_ratio,
                premium=selected.get("ask"),
                delta=selected.get("delta"),
                liquidity_score=10.0,
            )

            candidates.append(
                {
                    "symbol": chain.symbol,
                    "strategy_family": StrategyType.LONG_PUT.value,
                    "expiration": str(expiration),
                    "option_type": "PUT",
                    "strike": selected.get("strike"),
                    "delta": selected.get("delta"),
                    "bid": selected.get("bid"),
                    "ask": selected.get("ask"),
                    "premium": selected.get("ask"),
                    "score": score,
                }
            )

    candidates.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
    return candidates


def quote_to_dict(quote: object) -> dict[str, object]:
    return {
        "option_type": getattr(quote, "option_type", None),
        "strike": getattr(quote, "strike", None),
        "delta": getattr(quote, "delta", None),
        "bid": getattr(quote, "bid", None),
        "ask": getattr(quote, "ask", None),
        "open_interest": getattr(quote, "open_interest", None),
        "volume": getattr(quote, "volume", None),
        "iv": getattr(quote, "implied_volatility", None),
        "expiration": getattr(quote, "expiration", None),
    }
