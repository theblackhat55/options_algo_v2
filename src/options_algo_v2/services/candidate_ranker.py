from __future__ import annotations


def score_candidate(
    *,
    regime_fit: bool,
    directional_fit: bool,
    iv_fit: bool,
    liquidity_fit: bool,
    expected_move_fit: bool,
    is_extended: bool,
) -> float:
    score = 0.0

    if regime_fit:
        score += 20.0

    if directional_fit:
        score += 25.0

    if iv_fit:
        score += 20.0

    if liquidity_fit:
        score += 20.0

    if expected_move_fit:
        score += 15.0

    if is_extended:
        score -= 10.0

    return score
