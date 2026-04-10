from __future__ import annotations

from dataclasses import replace
from typing import Any

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.services.runtime_mode import is_mock_mode


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


def _infer_direction(decision: CandidateDecision) -> str:
    strategy_type = getattr(decision.candidate, "strategy_type", None)

    if strategy_type is None:
        return "neutral"

    strategy_value = str(getattr(strategy_type, "value", strategy_type) or "").strip().upper()

    if strategy_value.startswith("BULL_"):
        return "bullish"
    if strategy_value.startswith("BEAR_"):
        return "bearish"
    return "neutral"


def _build_adjustment(
    decision: CandidateDecision,
    context_row: dict[str, Any] | None,
) -> tuple[
    float,
    list[str],
    bool,
    list[str],
]:
    if not isinstance(context_row, dict) or not context_row.get("context_available"):
        # In mock mode treat missing context as a score penalty only — never hard reject.
        # In live mode apply the full -8.0 penalty but still no hard reject for missing
        # context alone; hard_reject is reserved for low-confidence + bad-regime combos.
        score_delta = -8.0 if not is_mock_mode() else -4.0
        return score_delta, ["options_context_missing"], False, ["options_context_missing"]

    direction = _infer_direction(decision)

    confidence = _to_float(context_row.get("confidence_score")) or 0.0
    regime = str(context_row.get("options_summary_regime") or "").strip().lower()
    expected_move_1d_pct = _to_float(context_row.get("expected_move_1d_pct"))
    pcr_oi = _to_float(context_row.get("pcr_oi"))
    pcr_volume = _to_float(context_row.get("pcr_volume"))
    skew_ratio = _to_float(context_row.get("skew_25d_put_call_ratio"))
    distance_to_gamma_flip_pct = _to_float(context_row.get("distance_to_gamma_flip_pct"))
    nearest_expiry_gamma_pct = _to_float(context_row.get("nearest_expiry_gamma_pct"))
    bid_ask_ratio = _to_float(context_row.get("nonzero_bid_ask_ratio")) or 0.0
    iv_ratio = _to_float(context_row.get("nonzero_iv_ratio")) or 0.0
    delta_ratio = _to_float(context_row.get("nonzero_delta_ratio")) or 0.0

    score_delta = 0.0
    reasons: list[str] = []
    advisory_reasons: list[str] = []
    hard_reject = False

    # Confidence
    if confidence < 0.50:
        score_delta -= 6.0
        reasons.append("options_context_low_confidence")
    elif confidence < 0.75:
        score_delta -= 2.0
        reasons.append("options_context_medium_confidence")
    elif confidence >= 0.90:
        score_delta += 1.0
        advisory_reasons.append("options_context_high_confidence")

    # Regime
    if regime == "thin":
        score_delta -= 10.0
        reasons.append("thin_options_regime")
    elif regime in {"limited", "illiquid"}:
        score_delta -= 6.0
        reasons.append("limited_options_regime")
    elif regime == "put_heavy_liquid":
        if direction == "bullish":
            score_delta -= 2.0
            reasons.append("regime_put_heavy")
        elif direction == "bearish":
            score_delta += 1.0
            advisory_reasons.append("regime_put_heavy_supportive")
    elif regime == "call_heavy_liquid":
        if direction == "bullish":
            score_delta += 1.0
            advisory_reasons.append("regime_call_heavy_supportive")
        elif direction == "bearish":
            score_delta -= 2.0
            reasons.append("regime_call_heavy")
    elif regime in {"broad_liquid", "balanced_liquid"}:
        score_delta += 1.0
        advisory_reasons.append("liquid_options_regime")
    elif regime == "tradable":
        advisory_reasons.append("tradable_options_regime")

    # Expected move uses decimal fraction units, e.g. 0.025 = 2.5%
    if expected_move_1d_pct is not None:
        if expected_move_1d_pct < 0.015:
            score_delta -= 8.0
            reasons.append("expected_move_extremely_small")
        elif expected_move_1d_pct < 0.0225:
            score_delta -= 4.0
            reasons.append("expected_move_too_small")
        elif expected_move_1d_pct < 0.035:
            advisory_reasons.append("expected_move_neutral")
        elif expected_move_1d_pct < 0.05:
            score_delta += 2.0
            advisory_reasons.append("expected_move_supportive")
        else:
            score_delta += 4.0
            advisory_reasons.append("expected_move_strong")

    # PCR OI
    if pcr_oi is not None:
        if direction == "bullish":
            if pcr_oi >= 3.0:
                score_delta -= 5.0
                reasons.append("pcr_oi_extreme_put_heavy")
            elif pcr_oi >= 1.5:
                score_delta -= 2.0
                reasons.append("pcr_oi_put_heavy")
            elif pcr_oi < 0.35:
                score_delta += 2.0
                advisory_reasons.append("pcr_oi_call_heavy_supportive")
        elif direction == "bearish":
            if pcr_oi >= 3.0:
                score_delta += 1.0
                advisory_reasons.append("pcr_oi_put_heavy_supportive")
            elif pcr_oi < 0.35:
                score_delta -= 4.0
                reasons.append("pcr_oi_extreme_call_heavy")
            elif pcr_oi < 0.65:
                score_delta -= 2.0
                reasons.append("pcr_oi_call_heavy")

    # PCR volume
    if pcr_volume is not None:
        if direction == "bullish":
            if pcr_volume >= 2.5:
                score_delta -= 3.0
                reasons.append("pcr_volume_extreme_put_heavy")
            elif pcr_volume >= 1.5:
                score_delta -= 1.0
                advisory_reasons.append("pcr_volume_put_heavy_advisory")
            elif pcr_volume < 0.35:
                score_delta += 1.0
                advisory_reasons.append("pcr_volume_call_heavy_supportive")
        elif direction == "bearish":
            if pcr_volume >= 2.5:
                score_delta += 1.0
                advisory_reasons.append("pcr_volume_put_heavy_supportive")
            elif pcr_volume < 0.35:
                score_delta -= 2.0
                reasons.append("pcr_volume_extreme_call_heavy")

    # Skew
    if skew_ratio is not None:
        if direction == "bullish":
            if skew_ratio >= 2.0:
                score_delta -= 5.0
                reasons.append("extreme_put_skew")
            elif skew_ratio >= 1.3:
                score_delta -= 2.0
                reasons.append("elevated_put_skew")
            elif skew_ratio < 0.8:
                score_delta += 1.0
                advisory_reasons.append("call_skew_supportive")
        elif direction == "bearish":
            if skew_ratio >= 2.0:
                score_delta += 1.0
                advisory_reasons.append("put_skew_supportive")
            elif skew_ratio < 0.8:
                score_delta -= 3.0
                reasons.append("call_skew_extreme")

    # Gamma structure advisories
    if distance_to_gamma_flip_pct is not None:
        if distance_to_gamma_flip_pct < 0.005:
            score_delta -= 1.0
            advisory_reasons.append("very_near_gamma_flip")
        elif distance_to_gamma_flip_pct < 0.01:
            advisory_reasons.append("near_gamma_flip")

    if nearest_expiry_gamma_pct is not None:
        if nearest_expiry_gamma_pct >= 0.90:
            score_delta -= 1.0
            advisory_reasons.append("front_expiry_gamma_extreme")
        elif nearest_expiry_gamma_pct >= 0.75:
            advisory_reasons.append("front_expiry_gamma_concentrated")

    # Coverage quality
    if bid_ask_ratio < 0.80:
        score_delta -= 3.0
        reasons.append("weak_bid_ask_coverage")

    if iv_ratio < 0.70:
        score_delta -= 2.0
        reasons.append("weak_iv_coverage")

    if delta_ratio < 0.70:
        score_delta -= 2.0
        reasons.append("weak_delta_coverage")

    # Narrow hard reject rule
    if confidence < 0.50 and regime in {"thin", "limited", "illiquid"}:
        hard_reject = True
        reasons.append("options_context_untradable")

    return score_delta, reasons, hard_reject, advisory_reasons


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
        direction = _infer_direction(decision)
        score_delta, extra_reasons, hard_reject, advisory_reasons = _build_adjustment(
            decision,
            context_row,
        )

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
            "direction": direction,
            "context_available": bool(context_row.get("context_available")),
            "score_delta": round(score_delta, 3),
            "hard_reject": hard_reject,
            "applied_reason_codes": extra_reasons,
            "advisory_reason_codes": advisory_reasons,
            "final_score_after_context": new_final_score,
            "final_passed_after_context": final_passed,
            "options_summary_regime": context_row.get("options_summary_regime"),
            "confidence_score": context_row.get("confidence_score"),
            "expected_move_1d_pct": context_row.get("expected_move_1d_pct"),
            "pcr_oi": context_row.get("pcr_oi"),
            "pcr_volume": context_row.get("pcr_volume"),
            "skew_25d_put_call_ratio": context_row.get("skew_25d_put_call_ratio"),
            "distance_to_gamma_flip_pct": context_row.get("distance_to_gamma_flip_pct"),
            "nearest_expiry_gamma_pct": context_row.get("nearest_expiry_gamma_pct"),
        }

    return adjusted, debug
