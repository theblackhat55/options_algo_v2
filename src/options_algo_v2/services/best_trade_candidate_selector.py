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


def _candidate_score(item: dict[str, object]) -> float:
    width = _to_float(item.get("width", 0.0))
    net_credit = _to_float(item.get("net_credit", 0.0))
    net_debit = _to_float(item.get("net_debit", 0.0))
    strategy_family = str(item.get("strategy_family", ""))

    if width <= 0:
        return 0.0

    if strategy_family == "BULL_PUT_SPREAD":
        return min(1.0, net_credit / width)

    if strategy_family == "BULL_CALL_SPREAD":
        return max(0.0, 1.0 - (net_debit / width))

    return 0.0


def select_best_trade_candidate_per_symbol(
    trade_candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    best_by_symbol: dict[str, dict[str, object]] = {}

    for item in trade_candidates:
        symbol = str(item.get("symbol", "unknown"))
        enriched = dict(item)
        enriched["selection_score"] = round(_candidate_score(item), 4)

        existing = best_by_symbol.get(symbol)
        if existing is None:
            best_by_symbol[symbol] = enriched
            continue

        existing_score = _to_float(existing.get("selection_score", 0.0))
        current_score = _to_float(enriched.get("selection_score", 0.0))
        if current_score > existing_score:
            best_by_symbol[symbol] = enriched

    return sorted(
        best_by_symbol.values(),
        key=lambda item: _to_float(item.get("selection_score", 0.0)),
        reverse=True,
    )
