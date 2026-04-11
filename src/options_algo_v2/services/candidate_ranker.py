from __future__ import annotations


def _scale(value: float, low: float, high: float) -> float:
    """Linearly scale *value* into [0, 1] between *low* and *high*."""
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def score_candidate(
    *,
    regime_fit: bool,
    directional_fit: bool,
    iv_fit: bool,
    liquidity_fit: bool,
    expected_move_fit: bool,
    is_extended: bool,
    # Continuous inputs (optional — backward compatible)
    adx: float | None = None,
    iv_ratio: float | None = None,
    breadth_distance: float | None = None,
    momentum_score: float | None = None,
) -> float:
    """Score a candidate using a blend of boolean and continuous inputs.

    When continuous values are provided, they replace their boolean
    counterparts with a scaled 0-1 score for finer discrimination.
    """

    # --- Regime (20 pts max) ---
    if breadth_distance is not None:
        # breadth_distance: % away from the 50% dead-zone center.
        # Higher distance = clearer regime. Scale 0-20 over 0-15 pct.
        regime_score = 20.0 * _scale(breadth_distance, 0.0, 15.0)
    else:
        regime_score = 20.0 if regime_fit else 0.0

    # --- Directional (25 pts max) ---
    if adx is not None:
        # ADX: 18 = minimum trend, 40+ = very strong.
        # Scale [18, 40] -> [0, 1]
        directional_score = 25.0 * _scale(adx, 18.0, 40.0)
    else:
        directional_score = 25.0 if directional_fit else 0.0

    # --- IV (20 pts max) ---
    if iv_ratio is not None:
        # iv_hv_ratio: 1.0 = fair, 1.25+ = rich (good for selling premium).
        # Scale [1.0, 1.5] -> [0, 1]
        iv_score = 20.0 * _scale(iv_ratio, 1.0, 1.5)
    else:
        iv_score = 20.0 if iv_fit else 0.0

    # --- Liquidity (20 pts max) ---
    liquidity_score = 20.0 if liquidity_fit else 0.0

    # --- Expected move (15 pts max) ---
    if momentum_score is not None:
        move_score = 15.0 * max(0.0, min(1.0, momentum_score))
    else:
        move_score = 15.0 if expected_move_fit else 0.0

    total = regime_score + directional_score + iv_score + liquidity_score + move_score

    if is_extended:
        total -= 10.0

    return round(max(0.0, total), 2)


def score_candidate_breakdown(
    *,
    regime_fit: bool,
    directional_fit: bool,
    iv_fit: bool,
    liquidity_fit: bool,
    expected_move_fit: bool,
    is_extended: bool,
    adx: float | None = None,
    iv_ratio: float | None = None,
    breadth_distance: float | None = None,
    momentum_score: float | None = None,
) -> dict[str, float]:
    if breadth_distance is not None:
        regime_score = 20.0 * _scale(breadth_distance, 0.0, 15.0)
    else:
        regime_score = 20.0 if regime_fit else 0.0

    if adx is not None:
        directional_score = 25.0 * _scale(adx, 18.0, 40.0)
    else:
        directional_score = 25.0 if directional_fit else 0.0

    if iv_ratio is not None:
        iv_score = 20.0 * _scale(iv_ratio, 1.0, 1.5)
    else:
        iv_score = 20.0 if iv_fit else 0.0

    liquidity_score = 20.0 if liquidity_fit else 0.0

    if momentum_score is not None:
        move_score = 15.0 * max(0.0, min(1.0, momentum_score))
    else:
        move_score = 15.0 if expected_move_fit else 0.0

    extension_penalty = -10.0 if is_extended else 0.0
    base_total_score = regime_score + directional_score + iv_score + liquidity_score + move_score + extension_penalty

    return {
        "regime_score": round(regime_score, 3),
        "directional_score": round(directional_score, 3),
        "iv_score": round(iv_score, 3),
        "liquidity_score": round(liquidity_score, 3),
        "move_score": round(move_score, 3),
        "extension_penalty": round(extension_penalty, 3),
        "base_total_score": round(max(0.0, base_total_score), 3),
    }
