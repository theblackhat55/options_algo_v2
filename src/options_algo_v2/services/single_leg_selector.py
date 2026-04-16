from __future__ import annotations

from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _contract_liquidity_score(contract: dict[str, Any]) -> float:
    bid = _safe_float(contract.get("bid")) or 0.0
    ask = _safe_float(contract.get("ask")) or 0.0
    delta = abs(_safe_float(contract.get("delta")) or 0.0)
    oi = _safe_float(contract.get("open_interest")) or 0.0
    volume = _safe_float(contract.get("volume")) or 0.0
    iv = _safe_float(contract.get("iv")) or 0.0

    if bid <= 0 or ask <= 0 or iv <= 0:
        return -1e9

    mid = (bid + ask) / 2.0
    width_pct = ((ask - bid) / mid) if mid > 0 else 999.0

    score = 0.0
    score -= width_pct * 100.0
    score += min(oi, 5000.0) / 250.0
    score += min(volume, 5000.0) / 250.0
    score += delta * 10.0
    return score


def select_long_call_contract(
    contracts: list[dict[str, Any]],
    *,
    min_abs_delta: float = 0.45,
    max_abs_delta: float = 0.65,
) -> dict[str, Any] | None:
    eligible: list[tuple[float, dict[str, Any]]] = []

    for contract in contracts:
        if str(contract.get("option_type", "")).upper() != "CALL":
            continue

        delta = abs(_safe_float(contract.get("delta")) or 0.0)
        if not (min_abs_delta <= delta <= max_abs_delta):
            continue

        score = _contract_liquidity_score(contract)
        if score <= -1e8:
            continue

        eligible.append((score, contract))

    if not eligible:
        return None

    eligible.sort(key=lambda item: item[0], reverse=True)
    return eligible[0][1]


def select_long_put_contract(
    contracts: list[dict[str, Any]],
    *,
    min_abs_delta: float = 0.45,
    max_abs_delta: float = 0.65,
) -> dict[str, Any] | None:
    eligible: list[tuple[float, dict[str, Any]]] = []

    for contract in contracts:
        if str(contract.get("option_type", "")).upper() != "PUT":
            continue

        delta = abs(_safe_float(contract.get("delta")) or 0.0)
        if not (min_abs_delta <= delta <= max_abs_delta):
            continue

        score = _contract_liquidity_score(contract)
        if score <= -1e8:
            continue

        eligible.append((score, contract))

    if not eligible:
        return None

    eligible.sort(key=lambda item: item[0], reverse=True)
    return eligible[0][1]
