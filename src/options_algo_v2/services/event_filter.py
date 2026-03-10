from __future__ import annotations

from datetime import date

from options_algo_v2.domain.qualification import QualificationResult


def passes_event_filter(
    *,
    earnings_date: date | None,
    planned_latest_exit: date,
) -> QualificationResult:
    if earnings_date is None:
        return QualificationResult(passed=True, reasons=[])

    if earnings_date <= planned_latest_exit:
        return QualificationResult(
            passed=False,
            reasons=["earnings event occurs before planned exit"],
        )

    return QualificationResult(passed=True, reasons=[])
