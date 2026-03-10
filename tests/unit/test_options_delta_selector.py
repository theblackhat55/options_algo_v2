from __future__ import annotations

from options_algo_v2.domain.options_chain import OptionQuote
from options_algo_v2.services.options_delta_selector import (
    filter_quotes_by_delta_band,
    select_quotes_nearest_delta,
)


def _make_quote(
    *,
    option_symbol: str,
    delta: float,
) -> OptionQuote:
    return OptionQuote(
        symbol="AAPL",
        option_symbol=option_symbol,
        expiration="2026-04-17",
        strike=100.0,
        option_type="PUT",
        bid=2.0,
        ask=2.2,
        mid=2.1,
        delta=delta,
        open_interest=1000,
        volume=200,
    )


def test_select_quotes_nearest_delta_returns_best_matches() -> None:
    quotes = [
        _make_quote(option_symbol="Q1", delta=-0.12),
        _make_quote(option_symbol="Q2", delta=-0.26),
        _make_quote(option_symbol="Q3", delta=-0.31),
    ]

    selected = select_quotes_nearest_delta(
        quotes,
        target_delta=0.28,
        top_n=2,
    )

    assert [quote.option_symbol for quote in selected] == ["Q2", "Q3"]


def test_filter_quotes_by_delta_band_filters_range() -> None:
    quotes = [
        _make_quote(option_symbol="Q1", delta=-0.12),
        _make_quote(option_symbol="Q2", delta=-0.26),
        _make_quote(option_symbol="Q3", delta=-0.31),
    ]

    selected = filter_quotes_by_delta_band(
        quotes,
        min_abs_delta=0.20,
        max_abs_delta=0.30,
    )

    assert [quote.option_symbol for quote in selected] == ["Q2"]
