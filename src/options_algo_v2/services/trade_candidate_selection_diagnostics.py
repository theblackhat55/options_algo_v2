from __future__ import annotations


def count_ranked_trade_candidates_by_strategy_family(
    ranked_candidates: list[dict[str, object]],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in ranked_candidates:
        strategy_family = str(item.get("strategy_family", "unknown"))
        counts[strategy_family] = counts.get(strategy_family, 0) + 1
    return counts


def list_ranked_trade_candidate_symbols(
    ranked_candidates: list[dict[str, object]],
) -> list[str]:
    return [str(item.get("symbol", "unknown")) for item in ranked_candidates]
