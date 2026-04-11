from __future__ import annotations

from collections import Counter

from options_algo_v2.domain.decision import CandidateDecision


def count_rejection_reasons(decisions: list[CandidateDecision]) -> dict[str, int]:
    counter: Counter[str] = Counter()

    for decision in decisions:
        for reason in decision.rejection_reasons:
            counter[reason] += 1

    return dict(sorted(counter.items()))


def count_signal_states(decisions: list[CandidateDecision]) -> dict[str, int]:
    counter = Counter(decision.candidate.signal_state.value for decision in decisions)
    return dict(sorted(counter.items()))


def count_strategy_types(decisions: list[CandidateDecision]) -> dict[str, int]:
    counter = Counter(decision.candidate.strategy_type.value for decision in decisions)
    return dict(sorted(counter.items()))

def count_directional_states(decisions: list[CandidateDecision]) -> dict[str, int]:
    counter = Counter(decision.candidate.directional_state.value for decision in decisions)
    return dict(sorted(counter.items()))


def count_non_actionable_directional_states(
    decisions: list[CandidateDecision],
) -> dict[str, int]:
    counter: Counter[str] = Counter()

    for decision in decisions:
        state = decision.candidate.directional_state.value
        if state in {"NEUTRAL", "NO_TRADE"}:
            counter[state] += 1

    return dict(sorted(counter.items()))


def list_non_actionable_directional_symbols(
    decisions: list[CandidateDecision],
    limit: int = 20,
) -> list[str]:
    symbols: list[str] = []

    for decision in decisions:
        state = decision.candidate.directional_state.value
        if state in {"NEUTRAL", "NO_TRADE"}:
            symbols.append(decision.candidate.symbol)

    return symbols[:limit]


def count_directional_blockers(
    serialized_decisions: list[dict[str, object]],
) -> dict[str, int]:
    counter: Counter[str] = Counter()

    for item in serialized_decisions:
        diagnostics = item.get("directional_diagnostics")
        if not isinstance(diagnostics, dict):
            continue

        blockers = diagnostics.get("directional_blockers")
        if not isinstance(blockers, list):
            continue

        for blocker in blockers:
            counter[str(blocker)] += 1

    return dict(sorted(counter.items()))



def count_blocking_reasons(serialized_decisions) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in serialized_decisions:
        reasons = item.get("blocking_reasons")
        if not isinstance(reasons, list):
            continue
        for reason in reasons:
            key = str(reason)
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def count_soft_penalty_reasons(serialized_decisions) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in serialized_decisions:
        reasons = item.get("soft_penalty_reasons")
        if not isinstance(reasons, list):
            continue
        for reason in reasons:
            key = str(reason)
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def list_passed_with_soft_penalties_symbols(
    serialized_decisions,
    limit: int = 20,
) -> list[str]:
    symbols: list[str] = []
    for item in serialized_decisions:
        if not item.get("final_passed"):
            continue
        soft = item.get("soft_penalty_reasons")
        symbol = item.get("symbol")
        if isinstance(symbol, str) and symbol and isinstance(soft, list) and len(soft) > 0:
            symbols.append(symbol)
    return symbols[:limit]


def list_near_threshold_failures(
    serialized_decisions,
    *,
    max_gap: float = 5.0,
    limit: int = 20,
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    for item in serialized_decisions:
        final_passed = bool(item.get("final_passed"))
        if final_passed:
            continue

        final_score = item.get("final_score")
        min_score_required = item.get("min_score_required")
        if not isinstance(final_score, (int, float)) or not isinstance(min_score_required, (int, float)):
            continue

        gap = float(min_score_required) - float(final_score)
        if gap < 0 or gap > max_gap:
            continue

        items.append(
            {
                "symbol": item.get("symbol"),
                "final_score": float(final_score),
                "min_score_required": float(min_score_required),
                "score_gap": round(gap, 3),
                "blocking_reasons": list(item.get("blocking_reasons") or []),
                "soft_penalty_reasons": list(item.get("soft_penalty_reasons") or []),
                "directional_state": item.get("directional_state"),
                "strategy_type": item.get("strategy_type"),
            }
        )

    items.sort(key=lambda x: (x["score_gap"], str(x.get("symbol", ""))))
    return items[:limit]


def count_score_gap_buckets(serialized_decisions) -> dict[str, int]:
    counts = {
        "below_0": 0,
        "0_to_2": 0,
        "2_to_5": 0,
        "5_to_10": 0,
        "10_plus": 0,
    }

    for item in serialized_decisions:
        if bool(item.get("final_passed")):
            continue

        final_score = item.get("final_score")
        min_score_required = item.get("min_score_required")
        if not isinstance(final_score, (int, float)) or not isinstance(min_score_required, (int, float)):
            continue

        gap = float(min_score_required) - float(final_score)
        if gap < 0:
            counts["below_0"] += 1
        elif gap <= 2:
            counts["0_to_2"] += 1
        elif gap <= 5:
            counts["2_to_5"] += 1
        elif gap <= 10:
            counts["5_to_10"] += 1
        else:
            counts["10_plus"] += 1

    return counts


def highest_score_failing_decision(serialized_decisions) -> dict[str, object] | None:
    failures = [
        item
        for item in serialized_decisions
        if not bool(item.get("final_passed")) and isinstance(item.get("final_score"), (int, float))
    ]
    if not failures:
        return None
    best = max(failures, key=lambda x: float(x.get("final_score", 0.0)))
    return {
        "symbol": best.get("symbol"),
        "final_score": best.get("final_score"),
        "min_score_required": best.get("min_score_required"),
        "blocking_reasons": list(best.get("blocking_reasons") or []),
        "soft_penalty_reasons": list(best.get("soft_penalty_reasons") or []),
        "directional_state": best.get("directional_state"),
        "strategy_type": best.get("strategy_type"),
    }


def lowest_score_passing_decision(serialized_decisions) -> dict[str, object] | None:
    passes = [
        item
        for item in serialized_decisions
        if bool(item.get("final_passed")) and isinstance(item.get("final_score"), (int, float))
    ]
    if not passes:
        return None
    worst = min(passes, key=lambda x: float(x.get("final_score", 0.0)))
    return {
        "symbol": worst.get("symbol"),
        "final_score": worst.get("final_score"),
        "min_score_required": worst.get("min_score_required"),
        "blocking_reasons": list(worst.get("blocking_reasons") or []),
        "soft_penalty_reasons": list(worst.get("soft_penalty_reasons") or []),
        "directional_state": worst.get("directional_state"),
        "strategy_type": worst.get("strategy_type"),
    }


def _review_row(item: dict[str, object]) -> dict[str, object]:
    return {
        "symbol": item.get("symbol"),
        "final_score": item.get("final_score"),
        "final_passed": item.get("final_passed"),
        "strategy_type": item.get("strategy_type"),
        "directional_state": item.get("directional_state"),
        "blocking_reasons": list(item.get("blocking_reasons") or []),
        "soft_penalty_reasons": list(item.get("soft_penalty_reasons") or []),
    }


def top_passed_decisions(
    serialized_decisions,
    *,
    limit: int = 5,
) -> list[dict[str, object]]:
    rows = [
        item for item in serialized_decisions
        if bool(item.get("final_passed")) and isinstance(item.get("final_score"), (int, float))
    ]
    rows.sort(key=lambda x: float(x.get("final_score", 0.0)), reverse=True)
    return [_review_row(item) for item in rows[:limit]]


def highest_score_failed_decisions(
    serialized_decisions,
    *,
    limit: int = 5,
) -> list[dict[str, object]]:
    rows = [
        item for item in serialized_decisions
        if not bool(item.get("final_passed")) and isinstance(item.get("final_score"), (int, float))
    ]
    rows.sort(key=lambda x: float(x.get("final_score", 0.0)), reverse=True)
    return [_review_row(item) for item in rows[:limit]]


def passed_with_soft_penalties_decisions(
    serialized_decisions,
    *,
    limit: int = 5,
) -> list[dict[str, object]]:
    rows = [
        item for item in serialized_decisions
        if bool(item.get("final_passed")) and len(list(item.get("soft_penalty_reasons") or [])) > 0
    ]
    rows.sort(key=lambda x: float(x.get("final_score", 0.0)), reverse=True)
    return [_review_row(item) for item in rows[:limit]]


def near_threshold_failure_decisions(
    serialized_decisions,
    *,
    max_gap: float = 5.0,
    limit: int = 5,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for item in serialized_decisions:
        if bool(item.get("final_passed")):
            continue

        final_score = item.get("final_score")
        min_score_required = item.get("min_score_required")
        if not isinstance(final_score, (int, float)) or not isinstance(min_score_required, (int, float)):
            continue

        gap = float(min_score_required) - float(final_score)
        if 0 <= gap <= max_gap:
            row = _review_row(item)
            row["score_gap"] = round(gap, 3)
            rows.append(row)

    rows.sort(key=lambda x: (float(x.get("score_gap", 999.0)), -float(x.get("final_score", 0.0))))
    return rows[:limit]


def classify_failure_archetype(item: dict[str, object]) -> str:
    if bool(item.get("final_passed")):
        return "passed"

    blocking = [str(x) for x in list(item.get("blocking_reasons") or [])]
    soft = [str(x) for x in list(item.get("soft_penalty_reasons") or [])]

    if "directional state is not actionable" in blocking:
        return "directional_non_actionable"
    if "option volume below minimum" in blocking:
        return "liquidity_blocked"
    if "strategy not permitted in current regime" in blocking:
        return "strategy_regime_mismatch"
    if blocking == ["candidate score below minimum threshold"] and not soft:
        return "score_only_failure"
    if "candidate score below minimum threshold" in blocking and soft:
        return "score_plus_soft_penalties"
    return "other_blocked"


def count_failure_archetypes(serialized_decisions) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in serialized_decisions:
        archetype = classify_failure_archetype(item)
        counts[archetype] = counts.get(archetype, 0) + 1
    return dict(sorted(counts.items()))


def failure_archetype_by_symbol(serialized_decisions) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in serialized_decisions:
        symbol = item.get("symbol")
        if isinstance(symbol, str) and symbol:
            result[symbol] = classify_failure_archetype(item)
    return dict(sorted(result.items()))


def failure_archetype_review_rows(
    serialized_decisions,
    *,
    archetype: str,
    limit: int = 5,
) -> list[dict[str, object]]:
    rows = [
        item
        for item in serialized_decisions
        if classify_failure_archetype(item) == archetype
    ]
    rows.sort(key=lambda x: float(x.get("final_score", 0.0)), reverse=True)
    return [_review_row(item) for item in rows[:limit]]


def failure_archetype_review_slices(
    serialized_decisions,
    *,
    limit: int = 5,
) -> dict[str, list[dict[str, object]]]:
    archetypes = [
        "directional_non_actionable",
        "liquidity_blocked",
        "score_plus_soft_penalties",
        "strategy_regime_mismatch",
        "score_only_failure",
        "other_blocked",
        "passed",
    ]
    return {
        archetype: failure_archetype_review_rows(
            serialized_decisions,
            archetype=archetype,
            limit=limit,
        )
        for archetype in archetypes
    }
