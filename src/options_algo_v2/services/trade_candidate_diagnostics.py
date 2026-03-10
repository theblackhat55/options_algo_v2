from __future__ import annotations

from typing import cast


def count_trade_candidates_by_strategy_family(
    candidates: list[dict[str, object]],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in candidates:
        key = str(item.get("strategy_family", "unknown"))
        counts[key] = counts.get(key, 0) + 1
    return counts


def count_trade_candidates_by_symbol(
    candidates: list[dict[str, object]],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in candidates:
        key = str(item.get("symbol", "unknown"))
        counts[key] = counts.get(key, 0) + 1
    return counts


def rank_trade_candidates_by_credit_to_width(
    candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    def ratio(item: dict[str, object]) -> float:
        width_value = cast(float | int | str, item.get("width", 0.0) or 0.0)
        credit_value = cast(float | int | str, item.get("net_credit", 0.0) or 0.0)

        width = float(width_value)
        credit = float(credit_value)

        if width <= 0.0:
            return -1.0
        return credit / width

    return sorted(candidates, key=ratio, reverse=True)
