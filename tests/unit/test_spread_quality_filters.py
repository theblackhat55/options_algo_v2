from options_algo_v2.domain.options_chain import OptionQuote
from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.spread_quality_filters import (
    has_positive_width,
    has_valid_net_debit_or_credit,
    passes_max_bid_ask_spread_width,
    passes_min_open_interest,
)


def _make_candidate() -> TradeCandidate:
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
    return TradeCandidate(
        symbol="AAPL",
        strategy_family="BULL_PUT_SPREAD",
        expiration="2026-04-17",
        short_leg=short_leg,
        long_leg=long_leg,
        net_debit=0.0,
        net_credit=1.0,
        width=5.0,
    )


def test_has_positive_width() -> None:
    assert has_positive_width(_make_candidate()) is True


def test_has_valid_net_debit_or_credit() -> None:
    assert has_valid_net_debit_or_credit(_make_candidate()) is True


def test_passes_min_open_interest() -> None:
    assert passes_min_open_interest(_make_candidate(), min_open_interest=900) is True
    assert passes_min_open_interest(_make_candidate(), min_open_interest=1500) is False


def test_passes_max_bid_ask_spread_width() -> None:
    assert passes_max_bid_ask_spread_width(
        _make_candidate(),
        max_spread_width=0.5,
    ) is True
    assert passes_max_bid_ask_spread_width(
        _make_candidate(),
        max_spread_width=0.2,
    ) is False
