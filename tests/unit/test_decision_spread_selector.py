from datetime import date, timedelta

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.decision_spread_selector import (
    select_spread_candidates_for_decision,
)
from options_algo_v2.services.options_chain_provider_factory import (
    MockOptionsChainProvider,
    _mock_expiration,
)


def test_select_spread_candidates_for_bull_call_decision() -> None:
    exp = _mock_expiration()
    exp_date = date.fromisoformat(exp)
    decision = evaluate_candidate_decision(
        CandidateEvaluationInput(
            symbol="AAPL",
            market_regime=MarketRegime.TREND_UP,
            directional_state=DirectionalState.BULLISH_CONTINUATION,
            iv_state=IVState.IV_NORMAL,
            earnings_date=None,
            planned_latest_exit=exp_date,
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
    chain = MockOptionsChainProvider().get_chain(symbol="AAPL")

    spreads = select_spread_candidates_for_decision(
        decision=decision,
        chain=chain,
        expiration=exp,
    )

    assert len(spreads) == 1
    assert spreads[0].strategy_family == "BULL_CALL_SPREAD"


def test_select_spread_candidates_for_bull_put_decision() -> None:
    exp = _mock_expiration()
    exp_date = date.fromisoformat(exp)
    decision = evaluate_candidate_decision(
        CandidateEvaluationInput(
            symbol="AAPL",
            market_regime=MarketRegime.TREND_UP,
            directional_state=DirectionalState.BULLISH_CONTINUATION,
            iv_state=IVState.IV_RICH,
            earnings_date=None,
            planned_latest_exit=exp_date,
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
    chain = MockOptionsChainProvider().get_chain(symbol="AAPL")

    spreads = select_spread_candidates_for_decision(
        decision=decision,
        chain=chain,
        expiration=exp,
    )

    assert len(spreads) == 1
    assert spreads[0].strategy_family == "BULL_PUT_SPREAD"
