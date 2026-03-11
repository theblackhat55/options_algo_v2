from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.options_spread_selector import (
    select_vertical_call_spread_candidates,
    select_vertical_put_spread_candidates,
)


def test_select_vertical_call_spread_candidates_returns_ordered_pairs() -> None:
    chain = OptionsChainSnapshot(
        symbol="AAPL",
        as_of="2026-03-10T21:00:00Z",
        source="mock",
        quotes=[
            OptionQuote(
                symbol="AAPL",
                option_symbol="AAPL_C145",
                expiration="2026-04-17",
                strike=145.0,
                option_type="call",
                bid=4.8,
                ask=5.2,
                mid=5.0,
                delta=0.42,
                open_interest=1200,
                volume=300,
            ),
            OptionQuote(
                symbol="AAPL",
                option_symbol="AAPL_C150",
                expiration="2026-04-17",
                strike=150.0,
                option_type="call",
                bid=2.8,
                ask=3.2,
                mid=3.0,
                delta=0.31,
                open_interest=1100,
                volume=280,
            ),
            OptionQuote(
                symbol="AAPL",
                option_symbol="AAPL_C155",
                expiration="2026-04-17",
                strike=155.0,
                option_type="call",
                bid=1.4,
                ask=1.8,
                mid=1.6,
                delta=0.20,
                open_interest=900,
                volume=200,
            ),
        ],
    )

    candidates = select_vertical_call_spread_candidates(
        chain=chain,
        expiration="2026-04-17",
    )

    assert len(candidates) == 2
    assert candidates[0].strategy_family == "BULL_CALL_SPREAD"
    assert candidates[0].long_leg.strike == 145.0
    assert candidates[0].short_leg.strike == 150.0
    assert candidates[1].long_leg.strike == 150.0
    assert candidates[1].short_leg.strike == 155.0


def test_select_vertical_put_spread_candidates_returns_descending_pairs() -> None:
    chain = OptionsChainSnapshot(
        symbol="AAPL",
        as_of="2026-03-10T21:00:00Z",
        source="mock",
        quotes=[
            OptionQuote(
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
            ),
            OptionQuote(
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
            ),
            OptionQuote(
                symbol="AAPL",
                option_symbol="AAPL_P125",
                expiration="2026-04-17",
                strike=125.0,
                option_type="put",
                bid=0.8,
                ask=1.0,
                mid=0.9,
                delta=-0.12,
                open_interest=700,
                volume=150,
            ),
        ],
    )

    candidates = select_vertical_put_spread_candidates(
        chain=chain,
        expiration="2026-04-17",
    )

    assert len(candidates) == 2
    assert candidates[0].strategy_family == "BULL_PUT_SPREAD"
    assert candidates[0].short_leg.strike == 135.0
    assert candidates[0].long_leg.strike == 130.0
    assert candidates[1].short_leg.strike == 130.0
    assert candidates[1].long_leg.strike == 125.0
