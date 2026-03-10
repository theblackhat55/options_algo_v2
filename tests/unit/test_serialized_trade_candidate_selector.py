from __future__ import annotations

from options_algo_v2.services.serialized_trade_candidate_selector import (
    rank_serialized_trade_candidates,
    select_top_serialized_trade_candidates,
)


def test_rank_serialized_trade_candidates_orders_by_selection_score() -> None:
    items = [
        {
            "symbol": "MSFT",
            "strategy_family": "BULL_PUT_SPREAD",
            "net_credit": 0.5,
            "net_debit": 0.0,
            "width": 5.0,
        },
        {
            "symbol": "AAPL",
            "strategy_family": "BULL_PUT_SPREAD",
            "net_credit": 1.0,
            "net_debit": 0.0,
            "width": 5.0,
        },
    ]

    ranked = rank_serialized_trade_candidates(items)

    assert ranked[0]["symbol"] == "AAPL"
    assert ranked[0]["selection_score"] > ranked[1]["selection_score"]


def test_select_top_serialized_trade_candidates_limits_length() -> None:
    items = [
        {
            "symbol": "AAPL",
            "strategy_family": "BULL_PUT_SPREAD",
            "net_credit": 1.0,
            "net_debit": 0.0,
            "width": 5.0,
        },
        {
            "symbol": "MSFT",
            "strategy_family": "BULL_PUT_SPREAD",
            "net_credit": 0.8,
            "net_debit": 0.0,
            "width": 5.0,
        },
    ]

    top = select_top_serialized_trade_candidates(items, top_n=1)

    assert len(top) == 1
    assert top[0]["symbol"] == "AAPL"
