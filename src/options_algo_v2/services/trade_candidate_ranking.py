from __future__ import annotations

from typing import cast

from options_algo_v2.services.spread_scoring import (
    score_bull_call_spread,
    score_bull_put_spread,
)


def score_trade_candidate(candidate: dict[str, object]) -> float:
    """Score a trade candidate using the spread scoring model.

    Falls back to the simple credit/width ratio if spread scoring inputs
    are not available (backward compatible).
    """
    strategy_family = str(candidate.get("strategy_family", ""))

    width_value = cast(float | int | str, candidate.get("width", 0.0) or 0.0)
    width = float(width_value)

    if width <= 0.0:
        return 0.0

    if strategy_family == "BULL_PUT_SPREAD":
        short_leg_delta = float(candidate.get("short_delta", 0.0) or 0.0)
        short_leg_oi = int(candidate.get("short_open_interest", 0) or 0)
        net_credit = float(candidate.get("net_credit", 0.0) or 0.0)

        if short_leg_delta != 0.0 or short_leg_oi > 0:
            breakdown = score_bull_put_spread(
                short_leg_delta=short_leg_delta,
                short_leg_open_interest=short_leg_oi,
                net_credit=net_credit,
                width=width,
            )
            return breakdown["total"]

        # Fallback: simple credit/width
        return net_credit / width if width > 0 else 0.0

    if strategy_family == "BULL_CALL_SPREAD":
        long_leg_delta = float(candidate.get("long_delta", 0.0) or 0.0)
        long_leg_oi = int(candidate.get("long_open_interest", 0) or 0)
        net_debit = float(candidate.get("net_debit", 0.0) or 0.0)

        if long_leg_delta != 0.0 or long_leg_oi > 0:
            breakdown = score_bull_call_spread(
                long_leg_delta=long_leg_delta,
                long_leg_open_interest=long_leg_oi,
                net_debit=net_debit,
                width=width,
            )
            return breakdown["total"]

        # Fallback: 1 - debit/width (lower debit = better)
        return max(0.0, 1.0 - net_debit / width) if width > 0 else 0.0

    # Generic fallback
    credit = float(cast(float | int | str, candidate.get("net_credit", 0.0) or 0.0))
    return credit / width


def rank_trade_candidates(
    candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    return sorted(
        candidates,
        key=score_trade_candidate,
        reverse=True,
    )


def select_top_trade_candidates(
    candidates: list[dict[str, object]],
    *,
    top_n: int,
) -> list[dict[str, object]]:
    if top_n <= 0:
        return []

    return rank_trade_candidates(candidates)[:top_n]
