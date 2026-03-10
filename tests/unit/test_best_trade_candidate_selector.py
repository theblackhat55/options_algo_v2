from __future__ import annotations

from options_algo_v2.services.best_trade_candidate_selector import (
    select_best_trade_candidate_per_symbol,
)


def test_select_best_trade_candidate_per_symbol_keeps_best_score() -> None:
    items = [
        {
            "symbol": "AAPL",
            "strategy_family": "BULL_PUT_SPREAD",
            "expiration": "2026-04-17",
            "net_credit": 0.8,
            "net_debit": 0.0,
            "width": 5.0,
        },
        {
            "symbol": "AAPL",
            "strategy_family": "BULL_PUT_SPREAD",
            "expiration": "2026-05-15",
            "net_credit": 1.1,
            "net_debit": 0.0,
            "width": 5.0,
        },
        {
            "symbol": "MSFT",
            "strategy_family": "BULL_PUT_SPREAD",
            "expiration": "2026-04-17",
            "net_credit": 1.0,
            "net_debit": 0.0,
            "width": 5.0,
        },
    ]

    selected = select_best_trade_candidate_per_symbol(items)

    assert len(selected) == 2
    assert selected[0]["symbol"] == "AAPL"
    assert selected[0]["expiration"] == "2026-05-15"
    assert selected[1]["symbol"] == "MSFT"
