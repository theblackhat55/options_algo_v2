from options_algo_v2.domain.options_chain import OptionQuote
from options_algo_v2.services.options_spread_selector import VerticalSpreadCandidate
from options_algo_v2.services.trade_candidate_builder import build_trade_candidate


def test_build_trade_candidate_from_bull_put_spread() -> None:
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

    spread = VerticalSpreadCandidate(
        symbol="AAPL",
        strategy_family="BULL_PUT_SPREAD",
        short_leg=short_leg,
        long_leg=long_leg,
    )

    candidate = build_trade_candidate(spread)

    assert candidate.symbol == "AAPL"
    assert candidate.strategy_family == "BULL_PUT_SPREAD"
    assert candidate.expiration == "2026-04-17"
    assert candidate.width == 5.0
    assert candidate.net_credit == 1.0
    assert candidate.net_debit == 0.0


def test_build_trade_candidate_from_bull_call_spread() -> None:
    short_leg = OptionQuote(
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
    )
    long_leg = OptionQuote(
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
    )

    spread = VerticalSpreadCandidate(
        symbol="AAPL",
        strategy_family="BULL_CALL_SPREAD",
        short_leg=short_leg,
        long_leg=long_leg,
    )

    candidate = build_trade_candidate(spread)

    assert candidate.width == 5.0
    assert candidate.net_credit == 2.0
    assert candidate.net_debit == 0.0
