from __future__ import annotations

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.options_expiration_selector import (
    group_quotes_by_expiration,
    select_expirations_by_preference,
)


def _make_quote(
    *,
    option_symbol: str,
    expiration: str,
) -> OptionQuote:
    return OptionQuote(
        symbol="AAPL",
        option_symbol=option_symbol,
        expiration=expiration,
        strike=100.0,
        option_type="CALL",
        bid=2.0,
        ask=2.2,
        mid=2.1,
        delta=0.3,
        open_interest=1000,
        volume=200,
    )


def test_group_quotes_by_expiration_groups_chain_quotes() -> None:
    chain = OptionsChainSnapshot(
        symbol="AAPL",
        as_of="2026-03-10T21:00:00Z",
        source="mock",
        quotes=[
            _make_quote(option_symbol="AAPL_1", expiration="2026-04-17"),
            _make_quote(option_symbol="AAPL_2", expiration="2026-04-17"),
            _make_quote(option_symbol="AAPL_3", expiration="2026-05-15"),
        ],
    )

    grouped = group_quotes_by_expiration(chain)

    assert set(grouped.keys()) == {"2026-04-17", "2026-05-15"}
    assert len(grouped["2026-04-17"]) == 2
    assert len(grouped["2026-05-15"]) == 1


def test_select_expirations_by_preference_returns_available_only() -> None:
    chain = OptionsChainSnapshot(
        symbol="AAPL",
        as_of="2026-03-10T21:00:00Z",
        source="mock",
        quotes=[
            _make_quote(option_symbol="AAPL_1", expiration="2026-04-17"),
            _make_quote(option_symbol="AAPL_2", expiration="2026-05-15"),
        ],
    )

    selected = select_expirations_by_preference(
        chain,
        preferred_expirations=["2026-06-19", "2026-05-15", "2026-04-17"],
    )

    assert selected == ["2026-05-15", "2026-04-17"]
