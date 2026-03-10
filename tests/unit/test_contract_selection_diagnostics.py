from __future__ import annotations

from options_algo_v2.services.contract_selection_diagnostics import (
    count_trade_candidates_by_expiration,
    count_trade_candidates_by_strategy_family,
)


def test_count_trade_candidates_by_expiration() -> None:
    items = [
        {"symbol": "AAPL", "expiration": "2026-04-17"},
        {"symbol": "MSFT", "expiration": "2026-04-17"},
        {"symbol": "NVDA", "expiration": "2026-05-15"},
    ]

    assert count_trade_candidates_by_expiration(items) == {
        "2026-04-17": 2,
        "2026-05-15": 1,
    }


def test_count_trade_candidates_by_strategy_family() -> None:
    items = [
        {"strategy_family": "BULL_PUT_SPREAD"},
        {"strategy_family": "BULL_PUT_SPREAD"},
        {"strategy_family": "BULL_CALL_SPREAD"},
    ]

    assert count_trade_candidates_by_strategy_family(items) == {
        "BULL_PUT_SPREAD": 2,
        "BULL_CALL_SPREAD": 1,
    }
