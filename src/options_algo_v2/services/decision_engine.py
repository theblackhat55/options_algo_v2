from __future__ import annotations

from options_algo_v2.config.rulebook_config import load_rulebook_configs
from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.enums import SignalState
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.candidate_ranker import score_candidate
from options_algo_v2.services.event_filter import passes_event_filter
from options_algo_v2.services.extension_filter import passes_extension_filter
from options_algo_v2.services.liquidity_filter import passes_liquidity_filter
from options_algo_v2.services.strategy_selector import select_strategy_candidate


def evaluate_candidate_decision(
    evaluation_input: CandidateEvaluationInput,
) -> CandidateDecision:
    config = load_rulebook_configs()
    risk = config.risk
    strategy = config.strategy
    min_score_required = float(risk["min_candidate_score"])

    candidate = select_strategy_candidate(
        symbol=evaluation_input.symbol,
        market_regime=evaluation_input.market_regime,
        directional_state=evaluation_input.directional_state,
        iv_state=evaluation_input.iv_state,
    )

    event_result = passes_event_filter(
        earnings_date=evaluation_input.earnings_date,
        planned_latest_exit=evaluation_input.planned_latest_exit,
    )

    liquidity_result = passes_liquidity_filter(
        underlying_price=evaluation_input.underlying_price,
        avg_daily_volume=evaluation_input.avg_daily_volume,
        option_open_interest=evaluation_input.option_open_interest,
        option_volume=evaluation_input.option_volume,
        bid=evaluation_input.bid,
        ask=evaluation_input.ask,
        option_quote_age_seconds=evaluation_input.option_quote_age_seconds,
        underlying_quote_age_seconds=evaluation_input.underlying_quote_age_seconds,
        min_underlying_price=float(risk["min_underlying_price"]),
        min_avg_daily_volume=float(risk["min_avg_daily_volume"]),
        min_option_open_interest=int(risk["min_option_open_interest"]),
        min_option_volume=int(risk["min_option_volume"]),
        max_bid_ask_spread_pct=float(risk["max_bid_ask_spread_pct"]),
        max_option_quote_age_seconds=int(risk["max_option_quote_age_seconds"]),
        max_underlying_quote_age_seconds=int(risk["max_underlying_quote_age_seconds"]),
    )

    extension_result = passes_extension_filter(
        directional_state=evaluation_input.directional_state,
        close=evaluation_input.close,
        dma20=evaluation_input.dma20,
        atr20=evaluation_input.atr20,
        extension_atr_multiple=float(strategy["extension_atr_multiple"]),
    )

    selector_passed = candidate.signal_state == SignalState.QUALIFIED
    hard_filters_passed = (
        event_result.passed
        and liquidity_result.passed
        and extension_result.passed
    )

    final_score = 0.0
    if selector_passed:
        final_score = score_candidate(
            regime_fit=True,
            directional_fit=True,
            iv_fit=True,
            liquidity_fit=liquidity_result.passed,
            expected_move_fit=evaluation_input.expected_move_fit,
            is_extended=not extension_result.passed,
        )

    rejection_reasons: list[str] = []

    if not selector_passed:
        rejection_reasons.extend(candidate.rationale)

    if not event_result.passed:
        rejection_reasons.extend(event_result.reasons)

    if not liquidity_result.passed:
        rejection_reasons.extend(liquidity_result.reasons)

    if not extension_result.passed:
        rejection_reasons.extend(extension_result.reasons)

    if selector_passed and hard_filters_passed and final_score < min_score_required:
        rejection_reasons.append("candidate score below minimum threshold")

    final_passed = (
        selector_passed
        and hard_filters_passed
        and final_score >= min_score_required
    )

    return CandidateDecision(
        candidate=candidate,
        event_result=event_result,
        liquidity_result=liquidity_result,
        extension_result=extension_result,
        final_passed=final_passed,
        final_score=final_score,
        min_score_required=min_score_required,
        close=evaluation_input.close,
        dma20=evaluation_input.dma20,
        dma50=evaluation_input.dma50,
        atr20=evaluation_input.atr20,
        adx14=evaluation_input.adx14,
        iv_rank=evaluation_input.iv_rank,
        iv_hv_ratio=evaluation_input.iv_hv_ratio,
        market_breadth_pct_above_20dma=evaluation_input.market_breadth_pct_above_20dma,
        rejection_reasons=rejection_reasons,
    )
