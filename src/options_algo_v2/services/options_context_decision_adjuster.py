from __future__ import annotations

from dataclasses import replace
from typing import Any

from options_algo_v2.domain.decision import CandidateDecision


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


def _build_adjustment(context_row: dict[str, Any] | None) -> tuple[float, list[str], bool]:
    if not isinstance(context_row, dict) or not context_row.get("context_available"):
        return -8.0, ["options_context_missing"], True

    confidence = _to_float(context_row.get("confidence_score")) or 0.0
    regime = str(context_row.get("options_summary_regime") or "").strip().lower()
    expected_move_1d_pct = _to_float(context_row.get("expected_move_1d_pct"))
    pcr_oi = _to_float(context_row.get("pcr_oi"))
    pcr_volume = _to_float(context_row.get("pcr_volume"))
    skew_ratio = _to_float(context_row.get("skew_25d_put_call_ratio"))
    bid_ask_ratio = _to_float(context_row.get("nonzero_bid_ask_ratio")) or 0.0
    iv_ratio = _to_float(context_row.get("nonzero_iv_ratio")) or 0.0
    delta_ratio = _to_float(context_row.get("nonzero_delta_ratio")) or 0.0

    score_delta = 0.0
    reasons: list[str] = []
    hard_reject = False

    if confidence < 0.50:
        score_delta -= 8.0
        reasons.append("options_context_low_confidence")
    elif confidence < 0.75:
        score_delta -= 4.0
        reasons.append("options_context_medium_confidence")
    else:
        score_delta += 2.0

    if regime == "thin":
        score_delta -= 10.0
        reasons.append("thin_options_regime")
    elif regime in {"limited", "illiquid"}:
        score_delta -= 6.0
        reasons.append("limited_options_regime")
    elif regime in {
        "tradable",
        "broad_liquid",
        "balanced_liquid",
        "call_heavy_liquid",
        "put_heavy_liquid",
    }:
        score_delta += 2.0

    if expected_move_1d_pct is not None and expected_move_1d_pct < 1.0:
        score_delta -= 4.0
        reasons.append("expected_move_too_small")

    if pcr_oi is not None and pcr_oi >= 1.75:
        score_delta -= 3.0
        reasons.append("pcr_oi_extreme_put_heavy")
    elif pcr_oi is not None and pcr_oi <= 0.55:
        score_delta -= 2.0
        reasons.append("pcr_oi_extreme_call_heavy")

    if pcr_volume is not None and pcr_volume >= 1.90:
        score_delta -= 2.0
        reasons.append("pcr_volume_extreme_put_heavy")
    elif pcr_volume is not None and pcr_volume <= 0.55:
        score_delta -= 1.0
        reasons.append("pcr_volume_extreme_call_heavy")

    if skew_ratio is not None and skew_ratio >= 1.20:
        score_delta -= 2.0
        reasons.append("extreme_put_skew")

    if bid_ask_ratio < 0.80:
        score_delta -= 3.0
        reasons.append("weak_bid_ask_coverage")

    if iv_ratio < 0.70:
        score_delta -= 2.0
        reasons.append("weak_iv_coverage")

    if delta_ratio < 0.70:
        score_delta -= 2.0
        reasons.append("weak_delta_coverage")

    if confidence < 0.50 and regime in {"thin", "limited", "illiquid"}:
        hard_reject = True
        reasons.append("options_context_untradable")

    return score_delta, reasons, hard_reject


def apply_options_context_to_decisions(
    decisions: list[CandidateDecision],
    *,
    options_context_by_symbol: dict[str, dict[str, Any]],
) -> tuple[list[CandidateDecision], dict[str, dict[str, Any]]]:
    adjusted: list[CandidateDecision] = []
    debug: dict[str, dict[str, Any]] = {}

    for decision in decisions:
        symbol = decision.candidate.symbol
        context_row = options_context_by_symbol.get(symbol, {})
        score_delta, extra_reasons, hard_reject = _build_adjustment(context_row)

        new_final_score = round(float(decision.final_score) + float(score_delta), 3)
        if new_final_score < 0.0:
            new_final_score = 0.0

        rejection_reasons = list(decision.rejection_reasons)
        for reason in extra_reasons:
            if reason not in rejection_reasons:
                rejection_reasons.append(reason)

        final_passed = bool(decision.final_passed)
        if hard_reject:
            final_passed = False
        elif final_passed and new_final_score < float(decision.min_score_required):
            final_passed = False
            if "candidate score below minimum threshold" not in rejection_reasons:
                rejection_reasons.append("candidate score below minimum threshold")

        adjusted_decision = replace(
            decision,
            final_score=new_final_score,
            final_passed=final_passed,
            rejection_reasons=rejection_reasons,
        )
        adjusted.append(adjusted_decision)

        debug[symbol] = {
            "symbol": symbol,
            "context_available": bool(context_row.get("context_available")),
            "score_delta": round(score_delta, 3),
            "hard_reject": hard_reject,
            "applied_reason_codes": extra_reasons,
            "final_score_after_context": new_final_score,
            "final_passed_after_context": final_passed,
            "options_summary_regime": context_row.get("options_summary_regime"),
            "confidence_score": context_row.get("confidence_score"),
            "expected_move_1d_pct": context_row.get("expected_move_1d_pct"),
            "pcr_oi": context_row.get("pcr_oi"),
            "pcr_volume": context_row.get("pcr_volume"),
            "skew_25d_put_call_ratio": context_row.get("skew_25d_put_call_ratio"),
        }

    return adjusted, debug
