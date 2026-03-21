from __future__ import annotations

from options_algo_v2.domain.decision import CandidateDecision


def _directional_checks(decision: CandidateDecision) -> dict[str, bool]:
    close_gt_dma20 = False
    if decision.close is not None and decision.dma20 is not None:
        close_value = decision.close
        dma20_value = decision.dma20
        close_gt_dma20 = close_value > dma20_value

    dma20_gt_dma50 = False
    if decision.dma20 is not None and decision.dma50 is not None:
        dma20_value = decision.dma20
        dma50_value = decision.dma50
        dma20_gt_dma50 = dma20_value > dma50_value

    adx14_gte_18 = False
    if decision.adx14 is not None:
        adx14_value = decision.adx14
        adx14_gte_18 = adx14_value >= 18.0

    return {
        "close_gt_dma20": close_gt_dma20,
        "dma20_gt_dma50": dma20_gt_dma50,
        "adx14_gte_18": adx14_gte_18,
    }


def serialize_candidate_decision(
    decision: CandidateDecision,
) -> dict[str, object]:
    return {
        "symbol": decision.candidate.symbol,
        "market_regime": decision.candidate.market_regime.value,
        "directional_state": decision.candidate.directional_state.value,
        "iv_state": decision.candidate.iv_state.value,
        "strategy_type": decision.candidate.strategy_type.value,
        "signal_state": decision.candidate.signal_state.value,
        "final_passed": decision.final_passed,
        "final_score": decision.final_score,
        "min_score_required": decision.min_score_required,
        "rejection_reasons": list(decision.rejection_reasons),
        "rationale": list(decision.candidate.rationale),
        "event_filter": {
            "passed": decision.event_result.passed,
            "reasons": list(decision.event_result.reasons),
        },
        "liquidity_filter": {
            "passed": decision.liquidity_result.passed,
            "reasons": list(decision.liquidity_result.reasons),
        },
        "extension_filter": {
            "passed": decision.extension_result.passed,
            "reasons": list(decision.extension_result.reasons),
        },
        "close": decision.close,
        "dma20": decision.dma20,
        "dma50": decision.dma50,
        "atr20": decision.atr20,
        "adx14": decision.adx14,
        "iv_rank": decision.iv_rank,
        "iv_hv_ratio": decision.iv_hv_ratio,
        "market_breadth_pct_above_20dma": decision.market_breadth_pct_above_20dma,
        "rsi14": decision.rsi14,
        "five_day_return": decision.five_day_return,
        "breakout_above_20d_high": decision.breakout_above_20d_high,
        "breakdown_below_20d_low": decision.breakdown_below_20d_low,
        "breakout_volume_multiple": decision.breakout_volume_multiple,
        "extended_up": decision.extended_up,
        "extended_down": decision.extended_down,
        "directional_checks": _directional_checks(decision),
    }
