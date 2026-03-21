from __future__ import annotations

from typing import cast

from options_algo_v2.services.spread_scoring import (
    score_bull_call_spread,
    score_bull_put_spread,
)


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value).strip()
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def _options_context_ranking_adjustment(candidate: dict[str, object]) -> float:
    score = 0.0

    confidence = _to_float(candidate.get("options_context_confidence_score")) or 0.0
    regime = str(candidate.get("options_context_regime") or "").strip().lower()
    expected_move = _to_float(candidate.get("options_context_expected_move_1d_pct"))
    skew_ratio = _to_float(candidate.get("options_context_skew_25d_put_call_ratio"))

    if confidence >= 0.75:
        score += 0.15
    elif confidence < 0.50:
        score -= 0.25

    if regime in {
        "tradable",
        "broad_liquid",
        "balanced_liquid",
        "call_heavy_liquid",
        "put_heavy_liquid",
    }:
        score += 0.10
    elif regime in {"thin", "limited", "illiquid"}:
        score -= 0.20

    if expected_move is not None and expected_move >= 1.5:
        score += 0.05
    elif expected_move is not None and expected_move < 1.0:
        score -= 0.10

    if skew_ratio is not None and skew_ratio >= 1.20:
        score -= 0.05

    return score


def score_trade_candidate(candidate: dict[str, object]) -> float:
    """Score a trade candidate using the spread scoring model.

    Falls back to the simple credit/width ratio if spread scoring inputs
    are not available (backward compatible).
    """
    strategy_family = str(candidate.get("strategy_family", ""))

    width_value = cast(float | int | str, candidate.get("width", 0.0) or 0.0)
    width = float(width_value)

    if width <= 0.0:
        return 0.0

    if strategy_family == "BULL_PUT_SPREAD":
        short_leg_delta = float(candidate.get("short_delta", 0.0) or 0.0)
        short_leg_oi = int(candidate.get("short_open_interest", 0) or 0)
        net_credit = float(candidate.get("net_credit", 0.0) or 0.0)

        if short_leg_delta != 0.0 or short_leg_oi > 0:
            breakdown = score_bull_put_spread(
                short_leg_delta=short_leg_delta,
                short_leg_open_interest=short_leg_oi,
                net_credit=net_credit,
                width=width,
            )
            return breakdown["total"] + _options_context_ranking_adjustment(candidate)

        # Fallback: simple credit/width
        base = net_credit / width if width > 0 else 0.0
        return base + _options_context_ranking_adjustment(candidate)

    if strategy_family == "BULL_CALL_SPREAD":
        long_leg_delta = float(candidate.get("long_delta", 0.0) or 0.0)
        long_leg_oi = int(candidate.get("long_open_interest", 0) or 0)
        net_debit = float(candidate.get("net_debit", 0.0) or 0.0)

        if long_leg_delta != 0.0 or long_leg_oi > 0:
            breakdown = score_bull_call_spread(
                long_leg_delta=long_leg_delta,
                long_leg_open_interest=long_leg_oi,
                net_debit=net_debit,
                width=width,
            )
            return breakdown["total"] + _options_context_ranking_adjustment(candidate)

        # Fallback: 1 - debit/width (lower debit = better)
        base = max(0.0, 1.0 - net_debit / width) if width > 0 else 0.0
        return base + _options_context_ranking_adjustment(candidate)

    # Generic fallback
    credit = float(cast(float | int | str, candidate.get("net_credit", 0.0) or 0.0))
    return (credit / width) + _options_context_ranking_adjustment(candidate)


def rank_trade_candidates(
    candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    return sorted(
        candidates,
        key=score_trade_candidate,
        reverse=True,
    )


def select_top_trade_candidates(
    candidates: list[dict[str, object]],
    *,
    top_n: int,
) -> list[dict[str, object]]:
    if top_n <= 0:
        return []

    return rank_trade_candidates(candidates)[:top_n]
