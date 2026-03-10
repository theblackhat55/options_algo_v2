from __future__ import annotations

from options_algo_v2.services.trade_candidate_selection_diagnostics import (
    count_ranked_trade_candidates_by_strategy_family,
    list_ranked_trade_candidate_symbols,
)


def test_count_ranked_trade_candidates_by_strategy_family() -> None:
    items = [
        {"symbol": "AAPL", "strategy_family": "BULL_PUT_SPREAD"},
        {"symbol": "MSFT", "strategy_family": "BULL_PUT_SPREAD"},
        {"symbol": "NVDA", "strategy_family": "BULL_CALL_SPREAD"},
    ]

    assert count_ranked_trade_candidates_by_strategy_family(items) == {
        "BULL_PUT_SPREAD": 2,
        "BULL_CALL_SPREAD": 1,
    }


def test_list_ranked_trade_candidate_symbols() -> None:
    items = [
        {"symbol": "AAPL", "strategy_family": "BULL_PUT_SPREAD"},
        {"symbol": "MSFT", "strategy_family": "BULL_PUT_SPREAD"},
    ]

    assert list_ranked_trade_candidate_symbols(items) == ["AAPL", "MSFT"]
