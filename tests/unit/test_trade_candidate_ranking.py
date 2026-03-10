from options_algo_v2.services.trade_candidate_ranking import (
    rank_trade_candidates,
    score_trade_candidate,
    select_top_trade_candidates,
)


def test_score_trade_candidate_returns_credit_to_width_ratio() -> None:
    candidate = {
        "symbol": "AAPL",
        "strategy_family": "BULL_PUT_SPREAD",
        "net_credit": 1.0,
        "width": 5.0,
    }

    assert score_trade_candidate(candidate) == 0.2


def test_score_trade_candidate_returns_zero_for_non_positive_width() -> None:
    candidate = {
        "symbol": "AAPL",
        "strategy_family": "BULL_PUT_SPREAD",
        "net_credit": 1.0,
        "width": 0.0,
    }

    assert score_trade_candidate(candidate) == 0.0


def test_rank_trade_candidates_orders_by_score_desc() -> None:
    candidates = [
        {"symbol": "AAPL", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 1.0, "width": 5.0},
        {"symbol": "MSFT", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 2.0, "width": 5.0},
        {"symbol": "NVDA", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 0.5, "width": 5.0},
    ]

    ranked = rank_trade_candidates(candidates)

    assert ranked[0]["symbol"] == "MSFT"
    assert ranked[1]["symbol"] == "AAPL"
    assert ranked[2]["symbol"] == "NVDA"


def test_select_top_trade_candidates_returns_top_n() -> None:
    candidates = [
        {"symbol": "AAPL", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 1.0, "width": 5.0},
        {"symbol": "MSFT", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 2.0, "width": 5.0},
        {"symbol": "NVDA", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 0.5, "width": 5.0},
    ]

    top = select_top_trade_candidates(candidates, top_n=2)

    assert len(top) == 2
    assert top[0]["symbol"] == "MSFT"
    assert top[1]["symbol"] == "AAPL"


def test_select_top_trade_candidates_returns_empty_for_non_positive_n() -> None:
    candidates = [
        {"symbol": "AAPL", "strategy_family": "BULL_PUT_SPREAD", "net_credit": 1.0, "width": 5.0},
    ]

    assert select_top_trade_candidates(candidates, top_n=0) == []
