from options_algo_v2.domain.options_chain import OptionQuote
from options_algo_v2.services.options_spread_selector import VerticalSpreadCandidate
from options_algo_v2.services.qualified_trade_candidate_builder import (
    build_qualified_trade_candidates,
)


def test_build_qualified_trade_candidates_returns_passing_candidate() -> None:
    short_leg = OptionQuote(
        symbol="AAPL",
        option_symbol="AAPL_P135",
        expiration="2026-04-17",
        strike=135.0,
        option_type="put",
        bid=2.3,
        ask=2.7,
        mid=2.5,
        delta=-0.28,
        open_interest=1400,
        volume=320,
    )
    long_leg = OptionQuote(
        symbol="AAPL",
        option_symbol="AAPL_P130",
        expiration="2026-04-17",
        strike=130.0,
        option_type="put",
        bid=1.3,
        ask=1.7,
        mid=1.5,
        delta=-0.19,
        open_interest=1000,
        volume=260,
    )

    spreads = [
        VerticalSpreadCandidate(
            symbol="AAPL",
            strategy_family="BULL_PUT_SPREAD",
            short_leg=short_leg,
            long_leg=long_leg,
        )
    ]

    candidates = build_qualified_trade_candidates(
        spreads,
        min_open_interest=900,
        max_bid_ask_spread_width=0.5,
    )

    assert len(candidates) == 1
    assert candidates[0].strategy_family == "BULL_PUT_SPREAD"
    assert candidates[0].net_credit == 1.0


def test_build_qualified_trade_candidates_filters_on_open_interest() -> None:
    short_leg = OptionQuote(
        symbol="AAPL",
        option_symbol="AAPL_P135",
        expiration="2026-04-17",
        strike=135.0,
        option_type="put",
        bid=2.3,
        ask=2.7,
        mid=2.5,
        delta=-0.28,
        open_interest=100,
        volume=320,
    )
    long_leg = OptionQuote(
        symbol="AAPL",
        option_symbol="AAPL_P130",
        expiration="2026-04-17",
        strike=130.0,
        option_type="put",
        bid=1.3,
        ask=1.7,
        mid=1.5,
        delta=-0.19,
        open_interest=100,
        volume=260,
    )

    spreads = [
        VerticalSpreadCandidate(
            symbol="AAPL",
            strategy_family="BULL_PUT_SPREAD",
            short_leg=short_leg,
            long_leg=long_leg,
        )
    ]

    candidates = build_qualified_trade_candidates(
        spreads,
        min_open_interest=900,
        max_bid_ask_spread_width=0.5,
    )

    assert candidates == []
