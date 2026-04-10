from __future__ import annotations

from typing import TypedDict


class TradeIdea(TypedDict):
    symbol: str
    strategy_type: str
    strategy_family: str
    expiration: str
    selected_expiration: str
    candidate_expirations_considered: list[str]
    option_type: str
    short_leg_option_symbol: str
    long_leg_option_symbol: str
    short_strike: float
    long_strike: float
    net_credit: float
    net_debit: float
    width: float
    max_risk: float
    score: float
    score_breakdown: dict[str, float]
    market_regime: str
    directional_state: str
    iv_state: str


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


def _extract_nested_str(item: dict[str, object], key: str, nested_key: str) -> str:
    nested = item.get(key)
    if not isinstance(nested, dict):
        return ""
    value = nested.get(nested_key)
    return str(value) if value is not None else ""


def _extract_nested_float(item: dict[str, object], key: str, nested_key: str) -> float:
    nested = item.get(key)
    if not isinstance(nested, dict):
        return 0.0
    return _to_float(nested.get(nested_key))


def build_trade_idea(
    *,
    trade_candidate: dict[str, object],
    decision: dict[str, object],
) -> TradeIdea:
    strategy_family = str(trade_candidate.get("strategy_family", "UNKNOWN"))
    expiration = str(trade_candidate.get("expiration", ""))
    width = _to_float(trade_candidate.get("width", 0.0))
    net_credit = _to_float(trade_candidate.get("net_credit", 0.0))
    net_debit = _to_float(trade_candidate.get("net_debit", 0.0))
    score = _to_float(trade_candidate.get("selection_score", 0.0))

    if strategy_family in {"BULL_PUT_SPREAD", "BEAR_CALL_SPREAD"}:
        max_risk = max(0.0, width - net_credit)
    elif strategy_family in {"BULL_CALL_SPREAD", "BEAR_PUT_SPREAD"}:
        max_risk = max(0.0, net_debit)
    else:
        max_risk = 0.0

    option_type = _extract_nested_str(trade_candidate, "short_leg", "option_type")

    return {
        "symbol": str(trade_candidate.get("symbol", "UNKNOWN")),
        "strategy_type": strategy_family,
        "strategy_family": strategy_family,
        "expiration": expiration,
        "selected_expiration": expiration,
        "candidate_expirations_considered": [expiration],
        "option_type": option_type,
        "short_leg_option_symbol": _extract_nested_str(
            trade_candidate, "short_leg", "option_symbol"
        ),
        "long_leg_option_symbol": _extract_nested_str(
            trade_candidate, "long_leg", "option_symbol"
        ),
        "short_strike": _extract_nested_float(trade_candidate, "short_leg", "strike"),
        "long_strike": _extract_nested_float(trade_candidate, "long_leg", "strike"),
        "net_credit": net_credit,
        "net_debit": net_debit,
        "width": width,
        "max_risk": round(max_risk, 4),
        "score": round(score, 4),
        "score_breakdown": {
            "selection_score": round(score, 4),
        },
        "market_regime": str(decision.get("market_regime", "UNKNOWN")),
        "directional_state": str(decision.get("directional_state", "UNKNOWN")),
        "iv_state": str(decision.get("iv_state", "UNKNOWN")),
    }


def build_trade_ideas(
    *,
    trade_candidates: list[dict[str, object]],
    decisions: list[dict[str, object]],
) -> list[TradeIdea]:
    decisions_by_symbol = {
        str(item.get("symbol", "UNKNOWN")): item for item in decisions
    }

    ideas: list[TradeIdea] = []
    for trade_candidate in trade_candidates:
        symbol = str(trade_candidate.get("symbol", "UNKNOWN"))
        decision = decisions_by_symbol.get(symbol)
        if decision is None:
            continue
        ideas.append(
            build_trade_idea(
                trade_candidate=trade_candidate,
                decision=decision,
            )
        )

    return ideas
