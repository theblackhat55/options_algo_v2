from __future__ import annotations

from datetime import date

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.expiration_aware_spread_selector import (
    select_spread_candidates_across_expirations,
)


def _make_quote(
    *,
    option_symbol: str,
    expiration: str,
    strike: float,
    option_type: str,
    bid: float,
    ask: float,
    delta: float,
) -> OptionQuote:
    return OptionQuote(
        symbol="AAPL",
        option_symbol=option_symbol,
        expiration=expiration,
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        mid=(bid + ask) / 2.0,
        delta=delta,
        open_interest=1200,
        volume=250,
    )


def test_select_spread_candidates_across_expirations_prefers_eligible_dte() -> None:
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

    chain = OptionsChainSnapshot(
        symbol="AAPL",
        as_of="2026-03-10T21:00:00Z",
        source="mock",
        quotes=[
            _make_quote(
                option_symbol="AAPL_P100_2026_04_17",
                expiration="2026-04-17",
                strike=100.0,
                option_type="PUT",
                bid=2.4,
                ask=2.6,
                delta=-0.28,
            ),
            _make_quote(
                option_symbol="AAPL_P95_2026_04_17",
                expiration="2026-04-17",
                strike=95.0,
                option_type="PUT",
                bid=1.4,
                ask=1.6,
                delta=-0.18,
            ),
            _make_quote(
                option_symbol="AAPL_P100_2026_06_19",
                expiration="2026-06-19",
                strike=100.0,
                option_type="PUT",
                bid=2.5,
                ask=2.7,
                delta=-0.29,
            ),
            _make_quote(
                option_symbol="AAPL_P95_2026_06_19",
                expiration="2026-06-19",
                strike=95.0,
                option_type="PUT",
                bid=1.5,
                ask=1.7,
                delta=-0.19,
            ),
        ],
    )

    spreads = select_spread_candidates_across_expirations(
        decision=decision,
        chain=chain,
        as_of_date=date(2026, 3, 10),
        min_dte=30,
        max_dte=60,
        target_dte=38,
    )

    assert len(spreads) == 1
    assert spreads[0].short_leg.expiration == "2026-04-17"
    assert spreads[0].strategy_family == "BULL_PUT_SPREAD"
