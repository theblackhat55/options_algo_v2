from __future__ import annotations

from options_algo_v2.domain.options_chain import OptionQuote
from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.trade_candidate_selector import (
    select_and_rank_trade_candidates,
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
        volume=250,
    )


def test_select_and_rank_trade_candidates_filters_and_orders() -> None:
    strong = TradeCandidate(
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
            open_interest=1800,
        ),
        long_leg=_make_quote(
            option_symbol="AAPL_P95",
            strike=95.0,
            option_type="PUT",
            bid=1.4,
            ask=1.6,
            delta=-0.18,
            open_interest=1200,
        ),
        width=5.0,
        net_debit=0.0,
        net_credit=1.0,
    )

    weak = TradeCandidate(
        symbol="MSFT",
        strategy_family="BULL_PUT_SPREAD",
        expiration="2026-04-17",
        short_leg=_make_quote(
            option_symbol="MSFT_P100",
            strike=100.0,
            option_type="PUT",
            bid=1.0,
            ask=1.2,
            delta=-0.10,
            open_interest=900,
        ),
        long_leg=_make_quote(
            option_symbol="MSFT_P95",
            strike=95.0,
            option_type="PUT",
            bid=0.5,
            ask=0.7,
            delta=-0.07,
            open_interest=700,
        ),
        width=5.0,
        net_debit=0.0,
        net_credit=0.5,
    )

    ranked = select_and_rank_trade_candidates([weak, strong])

    assert len(ranked) == 1
    assert ranked[0]["symbol"] == "AAPL"
    assert ranked[0]["strategy_family"] == "BULL_PUT_SPREAD"
    assert ranked[0]["score"] > 0.0
