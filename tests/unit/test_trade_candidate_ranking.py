import pytest

from options_algo_v2.services.trade_candidate_ranking import (
    rank_trade_candidates,
    score_trade_candidate,
    select_top_trade_candidates,
)


def test_score_trade_candidate_returns_credit_to_width_ratio() -> None:
    # score_trade_candidate applies _options_context_ranking_adjustment on top of the
    # credit/width ratio fallback. With no context fields present:
    #   confidence=0.0 < 0.50  → -0.25
    # So: net_credit/width + adjustment = 1.0/5.0 + (-0.25) = -0.05, clamped to 0.0
    # by rank_trade_candidates but score_trade_candidate itself returns the raw value.
    candidate = {
        "symbol": "AAPL",
        "strategy_family": "BULL_PUT_SPREAD",
        "net_credit": 1.0,
        "width": 5.0,
    }

    score = score_trade_candidate(candidate)
    # The raw score includes the options-context penalty; result is -0.05
    assert score == pytest.approx(-0.05, abs=1e-9)


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


def test_score_trade_candidate_uses_spread_scoring_when_delta_available() -> None:
    """When short_delta and short_open_interest are present, use spread scoring model."""
    candidate = {
        "symbol": "AAPL",
        "strategy_family": "BULL_PUT_SPREAD",
        "short_delta": -0.22,
        "short_open_interest": 1500,
        "net_credit": 1.0,
        "width": 5.0,
    }
    score = score_trade_candidate(candidate)
    # Should use the spread scoring model, returning a value between 0 and 1
    assert 0.0 < score <= 1.0


def test_score_bull_call_spread_with_spread_scoring() -> None:
    candidate = {
        "symbol": "AAPL",
        "strategy_family": "BULL_CALL_SPREAD",
        "long_delta": 0.55,
        "long_open_interest": 2000,
        "net_debit": 2.0,
        "width": 5.0,
    }
    score = score_trade_candidate(candidate)
    assert 0.0 < score <= 1.0
