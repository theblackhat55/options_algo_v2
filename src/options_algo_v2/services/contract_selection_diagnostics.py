from __future__ import annotations

from collections import Counter


def count_trade_candidates_by_expiration(
    trade_candidates: list[dict[str, object]],
) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in trade_candidates:
        counter[str(item.get("expiration", "unknown"))] += 1
    return dict(counter)


def count_trade_candidates_by_strategy_family(
    trade_candidates: list[dict[str, object]],
) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in trade_candidates:
        counter[str(item.get("strategy_family", "unknown"))] += 1
    return dict(counter)
