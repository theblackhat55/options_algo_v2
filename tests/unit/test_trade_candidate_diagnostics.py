from options_algo_v2.services.trade_candidate_diagnostics import (
    count_trade_candidates_by_strategy_family,
    count_trade_candidates_by_symbol,
    rank_trade_candidates_by_credit_to_width,
)


def test_count_trade_candidates_by_strategy_family() -> None:
    candidates = [
        {"symbol": "AAPL", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 1.0, "width": 5.0},
        {"symbol": "MSFT", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 0.8, "width": 5.0},
        {"symbol": "NVDA", "strategy_family": "BULL_CALL_SPREAD", "net_credit": 2.0, "width": 5.0},
    ]

    assert count_trade_candidates_by_strategy_family(candidates) == {
        "BULL_PUT_SPREAD": 2,
        "BULL_CALL_SPREAD": 1,
    }


def test_count_trade_candidates_by_symbol() -> None:
    candidates = [
        {"symbol": "AAPL", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 1.0, "width": 5.0},
        {"symbol": "AAPL", "strategy_family": "BULL_CALL_SPREAD", "net_credit": 0.8, "width": 5.0},
        {"symbol": "MSFT", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 2.0, "width": 5.0},
    ]

    assert count_trade_candidates_by_symbol(candidates) == {
        "AAPL": 2,
        "MSFT": 1,
    }


def test_rank_trade_candidates_by_credit_to_width() -> None:
    candidates = [
        {"symbol": "AAPL", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 1.0, "width": 5.0},
        {"symbol": "MSFT", "strategy_family": "BULL_CALL_SPREAD", "net_credit": 2.0, "width": 5.0},
        {"symbol": "NVDA", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 0.5, "width": 5.0},
    ]

    ranked = rank_trade_candidates_by_credit_to_width(candidates)

    assert ranked[0]["symbol"] == "MSFT"
    assert ranked[1]["symbol"] == "AAPL"
    assert ranked[2]["symbol"] == "NVDA"
