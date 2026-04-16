from __future__ import annotations

from typing import Any


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def score_long_call(
    *,
    expected_move_1d_pct: float | None,
    iv_rank: float | None,
    iv_hv_ratio: float | None,
    premium: float | None,
    delta: float | None,
    liquidity_score: float | None = None,
) -> float:
    score = 0.0

    if expected_move_1d_pct is not None:
        if expected_move_1d_pct >= 5.0:
            score += 30.0
        elif expected_move_1d_pct >= 3.5:
            score += 20.0
        elif expected_move_1d_pct >= 2.0:
            score += 10.0

    if iv_rank is not None:
        if iv_rank <= 40:
            score += 20.0
        elif iv_rank <= 60:
            score += 10.0
        else:
            score -= 10.0

    if iv_hv_ratio is not None:
        if iv_hv_ratio <= 1.05:
            score += 15.0
        elif iv_hv_ratio <= 1.20:
            score += 8.0
        else:
            score -= 8.0

    if premium is not None:
        if premium <= 3.0:
            score += 15.0
        elif premium <= 6.0:
            score += 8.0
        else:
            score -= 5.0

    if delta is not None:
        abs_delta = abs(delta)
        if 0.45 <= abs_delta <= 0.65:
            score += 15.0
        else:
            score -= 5.0

    if liquidity_score is not None:
        score += min(liquidity_score, 20.0)

    return round(score, 3)


def score_long_put(
    *,
    expected_move_1d_pct: float | None,
    iv_rank: float | None,
    iv_hv_ratio: float | None,
    premium: float | None,
    delta: float | None,
    liquidity_score: float | None = None,
) -> float:
    return score_long_call(
        expected_move_1d_pct=expected_move_1d_pct,
        iv_rank=iv_rank,
        iv_hv_ratio=iv_hv_ratio,
        premium=premium,
        delta=delta,
        liquidity_score=liquidity_score,
    )
