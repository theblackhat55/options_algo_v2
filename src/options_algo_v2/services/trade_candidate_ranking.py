from __future__ import annotations

from typing import cast


def score_trade_candidate(candidate: dict[str, object]) -> float:
    width_value = cast(float | int | str, candidate.get("width", 0.0) or 0.0)
    credit_value = cast(float | int | str, candidate.get("net_credit", 0.0) or 0.0)

    width = float(width_value)
    credit = float(credit_value)

    if width <= 0.0:
        return 0.0

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
