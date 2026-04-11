from __future__ import annotations

from options_algo_v2.domain.decision import CandidateDecision


def _directional_diagnostics(decision: CandidateDecision) -> dict[str, object]:
    close_gt_dma20 = False
    close_gt_dma50 = False
    close_lt_dma20 = False
    close_lt_dma50 = False
    dma20_gt_dma50 = False
    dma20_lt_dma50 = False
    adx14_gte_18 = False
    adx14_gte_16 = False
    rsi_in_bullish_range = False
    rsi_in_bearish_range = False
    breakout_volume_multiple_gte_1_5 = False

    if decision.close is not None and decision.dma20 is not None:
        close_gt_dma20 = decision.close > decision.dma20
        close_lt_dma20 = decision.close < decision.dma20

    if decision.close is not None and decision.dma50 is not None:
        close_gt_dma50 = decision.close > decision.dma50
        close_lt_dma50 = decision.close < decision.dma50

    if decision.dma20 is not None and decision.dma50 is not None:
        dma20_gt_dma50 = decision.dma20 > decision.dma50
        dma20_lt_dma50 = decision.dma20 < decision.dma50

    if decision.adx14 is not None:
        adx14_gte_18 = decision.adx14 >= 18.0
        adx14_gte_16 = decision.adx14 >= 16.0

    if decision.rsi14 is not None:
        rsi_in_bullish_range = 45.0 <= decision.rsi14 <= 85.0
        rsi_in_bearish_range = 10.0 <= decision.rsi14 <= 55.0

    if decision.breakout_volume_multiple is not None:
        breakout_volume_multiple_gte_1_5 = decision.breakout_volume_multiple >= 1.5

    bullish_setup_ready = (
        close_gt_dma20
        and adx14_gte_16
        and rsi_in_bullish_range
        and not bool(decision.extended_up)
    )

    bearish_setup_ready = (
        close_lt_dma20
        and adx14_gte_16
        and rsi_in_bearish_range
        and not bool(decision.extended_down)
    )

    actionable_directional_state = decision.candidate.directional_state.value not in {
        "NEUTRAL",
        "NO_TRADE",
    }

    blockers: list[str] = []

    if not close_gt_dma20 and not close_lt_dma20:
        blockers.append("close_not_separated_from_dma20")
    if not close_gt_dma50 and not close_lt_dma50:
        blockers.append("close_not_separated_from_dma50")
    if not adx14_gte_16:
        blockers.append("adx_below_trending_min")
    if decision.rsi14 is None:
        blockers.append("rsi_missing")
    elif not rsi_in_bullish_range and not rsi_in_bearish_range:
        blockers.append("rsi_outside_bull_bear_ranges")
    if bool(decision.extended_up):
        blockers.append("extended_up")
    if bool(decision.extended_down):
        blockers.append("extended_down")

    if not bullish_setup_ready:
        if not close_gt_dma20:
            blockers.append("bullish_not_above_20dma")
        if not rsi_in_bullish_range and decision.rsi14 is not None:
            blockers.append("bullish_rsi_not_in_range")

    if not bearish_setup_ready:
        if not close_lt_dma20:
            blockers.append("bearish_not_below_20dma")
        if not rsi_in_bearish_range and decision.rsi14 is not None:
            blockers.append("bearish_rsi_not_in_range")

    if (
        decision.candidate.directional_state.value == "BULLISH_BREAKOUT"
        and not bool(decision.breakout_above_20d_high)
    ):
        blockers.append("breakout_flag_missing")
    if (
        decision.candidate.directional_state.value == "BEARISH_BREAKDOWN"
        and not bool(decision.breakdown_below_20d_low)
    ):
        blockers.append("breakdown_flag_missing")

    return {
        "close_gt_dma20": close_gt_dma20,
        "close_gt_dma50": close_gt_dma50,
        "close_lt_dma20": close_lt_dma20,
        "close_lt_dma50": close_lt_dma50,
        "dma20_gt_dma50": dma20_gt_dma50,
        "dma20_lt_dma50": dma20_lt_dma50,
        "adx14_gte_18": adx14_gte_18,
        "adx14_gte_16": adx14_gte_16,
        "rsi_in_bullish_range": rsi_in_bullish_range,
        "rsi_in_bearish_range": rsi_in_bearish_range,
        "breakout_above_20d_high": bool(decision.breakout_above_20d_high),
        "breakdown_below_20d_low": bool(decision.breakdown_below_20d_low),
        "breakout_volume_multiple_gte_1_5": breakout_volume_multiple_gte_1_5,
        "extended_up": bool(decision.extended_up),
        "extended_down": bool(decision.extended_down),
        "bullish_setup_ready": bullish_setup_ready,
        "bearish_setup_ready": bearish_setup_ready,
        "actionable_directional_state": actionable_directional_state,
        "directional_blockers": blockers,
    }


def _blocking_reasons(decision: CandidateDecision) -> list[str]:
    blocking: list[str] = []

    for reason in list(decision.event_result.reasons):
        if reason not in blocking:
            blocking.append(reason)

    for reason in list(decision.liquidity_result.reasons):
        if reason not in blocking:
            blocking.append(reason)

    for reason in list(decision.extension_result.reasons):
        if reason not in blocking:
            blocking.append(reason)

    for reason in list(decision.rejection_reasons):
        if reason == "candidate score below minimum threshold":
            if reason not in blocking:
                blocking.append(reason)
        elif reason == "options_context_untradable":
            if reason not in blocking:
                blocking.append(reason)
        elif reason == "directional state is not actionable":
            if reason not in blocking:
                blocking.append(reason)
        elif reason == "strategy not permitted in current regime":
            if reason not in blocking:
                blocking.append(reason)

    return blocking


def _soft_penalty_reasons(decision: CandidateDecision) -> list[str]:
    blocking = set(_blocking_reasons(decision))
    soft: list[str] = []

    for reason in list(decision.rejection_reasons):
        if reason not in blocking and reason not in soft:
            soft.append(reason)

    return soft


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
        "score_breakdown": dict(decision.score_breakdown),
        "blocking_reasons": _blocking_reasons(decision),
        "soft_penalty_reasons": _soft_penalty_reasons(decision),
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
        "underlying_price": decision.underlying_price,
        "avg_daily_volume": decision.avg_daily_volume,
        "option_open_interest": decision.option_open_interest,
        "option_volume": decision.option_volume,
        "bid": decision.bid,
        "ask": decision.ask,
        "option_quote_age_seconds": decision.option_quote_age_seconds,
        "underlying_quote_age_seconds": decision.underlying_quote_age_seconds,
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
        "directional_diagnostics": _directional_diagnostics(decision),
    }
