from datetime import date

import pytest

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.scan_trade_candidate_builder import (
    build_serialized_trade_candidates,
)


def _make_passed_decision():
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
            bid=2.45,
            ask=2.55,
            option_quote_age_seconds=10,
            underlying_quote_age_seconds=2,
            close=150.0,
            dma20=148.0,
            atr20=3.5,
            expected_move_fit=True,
        )
    )
    assert decision.final_passed is True
    return decision


def _make_rejected_decision():
    return evaluate_candidate_decision(
        CandidateEvaluationInput(
            symbol="IWM",
            market_regime=MarketRegime.RANGE_UNCLEAR,
            directional_state=DirectionalState.NEUTRAL,
            iv_state=IVState.IV_NORMAL,
            earnings_date=None,
            planned_latest_exit=date(2026, 4, 17),
            underlying_price=200.0,
            avg_daily_volume=2_000_000,
            option_open_interest=2000,
            option_volume=400,
            bid=2.4,
            ask=2.6,
            option_quote_age_seconds=10,
            underlying_quote_age_seconds=2,
            close=200.0,
            dma20=200.0,
            atr20=3.5,
            expected_move_fit=True,
        )
    )


def test_build_serialized_trade_candidates_returns_candidates_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    payloads = build_serialized_trade_candidates(
        decisions=[_make_passed_decision()],
        expiration="2026-04-17",
        min_open_interest=900,
        max_bid_ask_spread_width=0.5,
    )

    assert len(payloads) == 1
    assert payloads[0]["symbol"] == "AAPL"
    assert payloads[0]["strategy_family"] in {
        "BULL_CALL_SPREAD",
        "BULL_PUT_SPREAD",
    }


def test_build_serialized_trade_candidates_skips_rejected_decisions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    payloads = build_serialized_trade_candidates(
        decisions=[_make_rejected_decision()],
        expiration="2026-04-17",
        min_open_interest=900,
        max_bid_ask_spread_width=0.5,
    )

    assert payloads == []
