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
