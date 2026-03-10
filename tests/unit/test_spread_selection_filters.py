from __future__ import annotations

from options_algo_v2.domain.options_chain import OptionQuote
from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.spread_selection_filters import (
    passes_bull_call_delta_filter,
    passes_bull_put_delta_filter,
    passes_credit_width_filter,
    passes_debit_width_filter,
)


def _make_quote(
    *,
    option_symbol: str,
    strike: float,
    option_type: str,
    bid: float,
    ask: float,
    delta: float,
    open_interest: int,
) -> OptionQuote:
    return OptionQuote(
        symbol="AAPL",
        option_symbol=option_symbol,
        expiration="2026-04-17",
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        mid=(bid + ask) / 2.0,
        delta=delta,
        open_interest=open_interest,
        volume=200,
    )


def test_passes_bull_put_delta_filter_accepts_target_delta() -> None:
    candidate = TradeCandidate(
        symbol="AAPL",
        strategy_family="BULL_PUT_SPREAD",
        expiration="2026-04-17",
        short_leg=_make_quote(
            option_symbol="AAPL_P100",
            strike=100.0,
            option_type="PUT",
            bid=2.4,
            ask=2.6,
            delta=-0.28,
            open_interest=1200,
        ),
        long_leg=_make_quote(
            option_symbol="AAPL_P95",
            strike=95.0,
            option_type="PUT",
            bid=1.4,
            ask=1.6,
            delta=-0.18,
            open_interest=1000,
        ),
        width=5.0,
        net_debit=0.0,
        net_credit=1.0,
    )

    assert passes_bull_put_delta_filter(candidate) is True
    assert passes_credit_width_filter(candidate) is True


def test_passes_bull_call_delta_filter_accepts_target_delta() -> None:
    candidate = TradeCandidate(
        symbol="AAPL",
        strategy_family="BULL_CALL_SPREAD",
        expiration="2026-04-17",
        short_leg=_make_quote(
            option_symbol="AAPL_C150",
            strike=150.0,
            option_type="CALL",
            bid=1.4,
            ask=1.6,
            delta=0.21,
            open_interest=1000,
        ),
        long_leg=_make_quote(
            option_symbol="AAPL_C145",
            strike=145.0,
            option_type="CALL",
            bid=4.8,
            ask=5.2,
            delta=0.36,
            open_interest=1400,
        ),
        width=5.0,
        net_debit=2.0,
        net_credit=0.0,
    )

    assert passes_bull_call_delta_filter(candidate) is True
    assert passes_debit_width_filter(candidate) is True
