from __future__ import annotations

from datetime import date
from typing import Any

from options_algo_v2.domain.options_chain import OptionsChainSnapshot
from options_algo_v2.services.single_leg_trade_candidates import (
    select_single_leg_trade_candidates,
)


def _extract_rationale_value(
    decision: object,
    key: str,
    default: Any = None,
) -> Any:
    rationale = getattr(decision, "rationale", None)

    if rationale is None:
        return default

    if isinstance(rationale, dict):
        return rationale.get(key, default)

    if isinstance(rationale, list):
        prefix = f"{key}="
        for item in rationale:
            text = str(item)
            if text == key:
                return True
            if text.startswith(prefix):
                raw = text[len(prefix):]
                if raw in {"True", "true"}:
                    return True
                if raw in {"False", "false"}:
                    return False
                return raw
        return default

    return default


def build_shadow_single_leg_debug(
    decision: object,
    options_chain: OptionsChainSnapshot | None,
) -> dict[str, Any]:
    qualified = bool(getattr(decision, "qualified", False))

    strategy_type = getattr(decision, "strategy_type", None)
    if strategy_type is None:
        candidate = getattr(decision, "candidate", None)
        strategy_type = getattr(candidate, "strategy_type", None)

    strategy_type_value = getattr(strategy_type, "value", str(strategy_type or ""))

    long_call_eligible = bool(
        _extract_rationale_value(decision, "long_call_alternative_eligible", False)
    )
    long_put_eligible = bool(
        _extract_rationale_value(decision, "long_put_alternative_eligible", False)
    )

    has_options_chain = options_chain is not None
    should_try = (
        long_call_eligible
        or long_put_eligible
        or strategy_type_value in {"LONG_CALL", "LONG_PUT"}
    )

    if not qualified:
        reason = "decision_not_qualified"
    elif not has_options_chain:
        reason = "missing_options_chain"
    elif not should_try:
        reason = "no_long_option_alternative_flag"
    else:
        reason = "ready"

    return {
        "qualified": qualified,
        "strategy_type": strategy_type_value,
        "long_call_eligible": long_call_eligible,
        "long_put_eligible": long_put_eligible,
        "has_options_chain": has_options_chain,
        "shadow_attempted": False,
        "shadow_candidate_count": 0,
        "reason": reason,
    }


def build_shadow_single_leg_candidates(
    decision: object,
    options_chain: OptionsChainSnapshot | None,
    as_of_date: date | None = None,
    limit: int = 1,
) -> list[dict[str, Any]]:
    if options_chain is None:
        return []

    if not getattr(decision, "qualified", False):
        return []

    strategy_type = getattr(decision, "strategy_type", None)
    strategy_type_value = getattr(strategy_type, "value", str(strategy_type or ""))

    long_call_eligible = bool(
        _extract_rationale_value(decision, "long_call_alternative_eligible", False)
    )
    long_put_eligible = bool(
        _extract_rationale_value(decision, "long_put_alternative_eligible", False)
    )

    should_try = (
        long_call_eligible
        or long_put_eligible
        or strategy_type_value in {"LONG_CALL", "LONG_PUT"}
    )
    if not should_try:
        return []

    try:
        candidates = select_single_leg_trade_candidates(
            decision=decision,
            options_chain=options_chain,
            as_of_date=as_of_date,
        )
    except Exception:
        return []

    if not candidates:
        return []

    return candidates[: max(1, int(limit))]
