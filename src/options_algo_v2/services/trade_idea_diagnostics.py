from __future__ import annotations

from collections import Counter


def count_trade_ideas_by_strategy_family(
    trade_ideas: list[dict[str, object]],
) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in trade_ideas:
        counter[str(item.get("strategy_family", "UNKNOWN"))] += 1
    return dict(counter)


def list_trade_idea_symbols(
    trade_ideas: list[dict[str, object]],
) -> list[str]:
    return [str(item.get("symbol", "UNKNOWN")) for item in trade_ideas]
