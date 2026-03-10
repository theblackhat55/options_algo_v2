from __future__ import annotations

from datetime import date

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.enums import SignalState
from options_algo_v2.services.candidate_ranker import score_candidate
from options_algo_v2.services.event_filter import passes_event_filter
from options_algo_v2.services.extension_filter import passes_extension_filter
from options_algo_v2.services.liquidity_filter import passes_liquidity_filter
from options_algo_v2.services.strategy_selector import select_strategy_candidate


def evaluate_candidate_decision(
    *,
    symbol: str,
    market_regime,
    directional_state,
    iv_state,
    earnings_date: date | None,
    planned_latest_exit: date,
    underlying_price: float,
    avg_daily_volume: float,
    option_open_interest: int,
    option_volume: int,
    bid: float,
    ask: float,
    option_quote_age_seconds: int,
    underlying_quote_age_seconds: int,
    close: float,
    dma20: float,
    atr20: float,
    expected_move_fit: bool,
) -> CandidateDecision:
    candidate = select_strategy_candidate(
        symbol=symbol,
        market_regime=market_regime,
        directional_state=directional_state,
        iv_state=iv_state,
    )

    if candidate.signal_state == SignalState.REJECTED:
        return CandidateDecision(
            candidate=candidate,
            event_result=passes_event_filter(
                earnings_date=None,
                planned_latest_exit=planned_latest_exit,
            ),
            liquidity_result=passes_liquidity_filter(
                underlying_price=underlying_price,
                avg_daily_volume=avg_daily_volume,
                option_open_interest=option_open_interest,
                option_volume=option_volume,
                bid=bid,
                ask=ask,
                option_quote_age_seconds=option_quote_age_seconds,
                underlying_quote_age_seconds=underlying_quote_age_seconds,
            ),
            extension_result=passes_extension_filter(
                directional_state=directional_state,
                close=close,
                dma20=dma20,
                atr20=atr20,
            ),
            final_passed=False,
            final_score=0.0,
            rejection_reasons=list(candidate.rationale),
        )

    event_result = passes_event_filter(
        earnings_date=earnings_date,
        planned_latest_exit=planned_latest_exit,
    )

    liquidity_result = passes_liquidity_filter(
        underlying_price=underlying_price,
        avg_daily_volume=avg_daily_volume,
        option_open_interest=option_open_interest,
        option_volume=option_volume,
        bid=bid,
        ask=ask,
        option_quote_age_seconds=option_quote_age_seconds,
        underlying_quote_age_seconds=underlying_quote_age_seconds,
    )

    extension_result = passes_extension_filter(
        directional_state=directional_state,
        close=close,
        dma20=dma20,
        atr20=atr20,
    )

    final_passed = (
        event_result.passed
        and liquidity_result.passed
        and extension_result.passed
    )

    final_score = score_candidate(
        regime_fit=True,
        directional_fit=True,
        iv_fit=True,
        liquidity_fit=liquidity_result.passed,
        expected_move_fit=expected_move_fit,
        is_extended=not extension_result.passed,
    )

    rejection_reasons: list[str] = []
    if not event_result.passed:
        rejection_reasons.extend(event_result.reasons)
    if not liquidity_result.passed:
        rejection_reasons.extend(liquidity_result.reasons)
    if not extension_result.passed:
        rejection_reasons.extend(extension_result.reasons)

    return CandidateDecision(
        candidate=candidate,
        event_result=event_result,
        liquidity_result=liquidity_result,
        extension_result=extension_result,
        final_passed=final_passed,
        final_score=final_score,
        rejection_reasons=rejection_reasons,
    )
