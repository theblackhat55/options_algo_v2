from options_algo_v2.domain.options_chain import OptionQuote
from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.trade_candidate_serializer import (
    serialize_trade_candidate,
)


def test_serialize_trade_candidate_returns_expected_structure() -> None:
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
    candidate = TradeCandidate(
        symbol="AAPL",
        strategy_family="BULL_PUT_SPREAD",
        expiration="2026-04-17",
        short_leg=short_leg,
        long_leg=long_leg,
        net_debit=0.0,
        net_credit=1.0,
        width=5.0,
    )

    payload = serialize_trade_candidate(candidate)

    assert payload["symbol"] == "AAPL"
    assert payload["strategy_family"] == "BULL_PUT_SPREAD"
    assert payload["expiration"] == "2026-04-17"
    assert payload["net_credit"] == 1.0
    assert payload["width"] == 5.0
    assert payload["short_leg"]["option_symbol"] == "AAPL_P135"
    assert payload["long_leg"]["option_symbol"] == "AAPL_P130"
