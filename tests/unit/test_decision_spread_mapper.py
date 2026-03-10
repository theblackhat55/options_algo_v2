from datetime import date

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.decision_spread_mapper import (
    get_target_spread_family,
)


def test_get_target_spread_family_returns_candidate_strategy_type() -> None:
    decision = evaluate_candidate_decision(
        CandidateEvaluationInput(
            symbol="AAPL",
            market_regime=MarketRegime.TREND_UP,
            directional_state=DirectionalState.BULLISH_CONTINUATION,
            iv_state=IVState.IV_NORMAL,
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

    assert get_target_spread_family(decision) == "BULL_CALL_SPREAD"
