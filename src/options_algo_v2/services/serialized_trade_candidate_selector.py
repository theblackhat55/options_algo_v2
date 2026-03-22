from __future__ import annotations


def _to_float(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return 0.0
        try:
            return float(stripped)
        except ValueError:
            return 0.0
    return 0.0


def _score_serialized_trade_candidate(item: dict[str, object]) -> float:
    strategy_family = str(item.get("strategy_family", ""))
    width = _to_float(item.get("width", 0.0))
    net_credit = _to_float(item.get("net_credit", 0.0))
    net_debit = _to_float(item.get("net_debit", 0.0))

    if width <= 0:
        return 0.0

    if strategy_family in {"BULL_PUT_SPREAD", "BEAR_CALL_SPREAD"}:
        return round(min(1.0, net_credit / width), 4)

    if strategy_family in {"BULL_CALL_SPREAD", "BEAR_PUT_SPREAD"}:
        return round(max(0.0, 1.0 - (net_debit / width)), 4)

    return 0.0


def rank_serialized_trade_candidates(
    items: list[dict[str, object]],
) -> list[dict[str, object]]:
    ranked: list[dict[str, object]] = []
    for item in items:
        enriched = dict(item)
        enriched["selection_score"] = _score_serialized_trade_candidate(item)
        ranked.append(enriched)
    return sorted(
        ranked,
        key=lambda item: _to_float(item.get("selection_score", 0.0)),
        reverse=True,
    )


def select_top_serialized_trade_candidates(
    items: list[dict[str, object]],
    *,
    top_n: int,
) -> list[dict[str, object]]:
    return rank_serialized_trade_candidates(items)[:top_n]
