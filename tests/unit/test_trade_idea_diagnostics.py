from __future__ import annotations

from options_algo_v2.services.trade_idea_diagnostics import (
    count_trade_ideas_by_strategy_family,
    list_trade_idea_symbols,
)


def test_count_trade_ideas_by_strategy_family() -> None:
    items = [
        {"symbol": "AAPL", "strategy_family": "BULL_PUT_SPREAD"},
        {"symbol": "MSFT", "strategy_family": "BULL_PUT_SPREAD"},
        {"symbol": "NVDA", "strategy_family": "BULL_CALL_SPREAD"},
    ]

    assert count_trade_ideas_by_strategy_family(items) == {
        "BULL_PUT_SPREAD": 2,
        "BULL_CALL_SPREAD": 1,
    }


def test_list_trade_idea_symbols() -> None:
    items = [
        {"symbol": "AAPL"},
        {"symbol": "MSFT"},
    ]

    assert list_trade_idea_symbols(items) == ["AAPL", "MSFT"]
