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
