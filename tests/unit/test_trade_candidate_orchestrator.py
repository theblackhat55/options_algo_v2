from datetime import date

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.options_chain_provider_factory import (
    MockOptionsChainProvider,
)
from options_algo_v2.services.trade_candidate_orchestrator import (
    build_trade_candidates_for_decision,
)


def test_build_trade_candidates_for_decision_returns_candidates() -> None:
    decision = evaluate_candidate_decision(
        CandidateEvaluationInput(
            symbol="AAPL",
            market_regime=MarketRegime.TREND_UP,
            directional_state=DirectionalState.BULLISH_CONTINUATION,
            iv_state=IVState.IV_RICH,
            earnings_date=None,
            planned_latest_exit=date(2026, 4, 17),
            underlying_price=150.0,
            avg_daily_volume=5_000_000,
            option_open_interest=2000,
            option_volume=400,
            bid=2.4,
            ask=2.6,
            option_quote_age_seconds=10,
            underlying_quote_age_seconds=2,
            close=150.0,
            dma20=148.0,
            atr20=3.5,
            expected_move_fit=True,
        )
    )

    candidates = build_trade_candidates_for_decision(
        decision=decision,
        options_chain_provider=MockOptionsChainProvider(),
        expiration="2026-04-17",
        min_open_interest=900,
        max_bid_ask_spread_width=0.5,
    )

    assert len(candidates) == 1
    assert candidates[0].symbol == "AAPL"
    assert candidates[0].strategy_family == "BULL_PUT_SPREAD"


def test_build_trade_candidates_for_decision_returns_empty_when_filtered_out() -> None:
    decision = evaluate_candidate_decision(
        CandidateEvaluationInput(
            symbol="AAPL",
            market_regime=MarketRegime.TREND_UP,
            directional_state=DirectionalState.BULLISH_CONTINUATION,
            iv_state=IVState.IV_RICH,
            earnings_date=None,
            planned_latest_exit=date(2026, 4, 17),
            underlying_price=150.0,
            avg_daily_volume=5_000_000,
            option_open_interest=2000,
            option_volume=400,
            bid=2.4,
            ask=2.6,
            option_quote_age_seconds=10,
            underlying_quote_age_seconds=2,
            close=150.0,
            dma20=148.0,
            atr20=3.5,
            expected_move_fit=True,
        )
    )

    candidates = build_trade_candidates_for_decision(
        decision=decision,
        options_chain_provider=MockOptionsChainProvider(),
        expiration="2026-04-17",
        min_open_interest=5000,
        max_bid_ask_spread_width=0.5,
    )

    assert candidates == []
