from __future__ import annotations

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.domain.pipeline_payload import PipelineEvaluationPayload
from options_algo_v2.services.decision_engine import evaluate_candidate_decision


def payload_to_evaluation_input(
    payload: PipelineEvaluationPayload,
) -> CandidateEvaluationInput:
    return CandidateEvaluationInput(
        symbol=payload.symbol,
        market_regime=payload.market_regime,
        directional_state=payload.directional_state,
        iv_state=payload.iv_state,
        earnings_date=payload.earnings_date,
        planned_latest_exit=payload.planned_latest_exit,
        underlying_price=payload.underlying_price,
        avg_daily_volume=payload.avg_daily_volume,
        option_open_interest=payload.option_open_interest,
        option_volume=payload.option_volume,
        bid=payload.bid,
        ask=payload.ask,
        option_quote_age_seconds=payload.option_quote_age_seconds,
        underlying_quote_age_seconds=payload.underlying_quote_age_seconds,
        close=payload.close,
        dma20=payload.dma20,
        dma50=payload.dma50,
        atr20=payload.atr20,
        adx14=payload.adx14,
        iv_rank=payload.iv_rank,
        iv_hv_ratio=payload.iv_hv_ratio,
        market_breadth_pct_above_20dma=payload.market_breadth_pct_above_20dma,
        expected_move_fit=payload.expected_move_fit,
    )


def evaluate_pipeline_payload(
    payload: PipelineEvaluationPayload,
) -> CandidateDecision:
    evaluation_input = payload_to_evaluation_input(payload)
    return evaluate_candidate_decision(evaluation_input)
