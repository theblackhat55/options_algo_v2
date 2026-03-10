from __future__ import annotations

from options_algo_v2.services.trade_idea_builder import (
    build_trade_idea,
    build_trade_ideas,
)


def test_build_trade_idea_returns_expected_shape() -> None:
    trade_candidate = {
        "symbol": "AAPL",
        "strategy_family": "BULL_PUT_SPREAD",
        "expiration": "2026-04-17",
        "short_leg": {
            "option_symbol": "AAPL_2026-04-17_P_100",
            "option_type": "PUT",
            "strike": 100.0,
        },
        "long_leg": {
            "option_symbol": "AAPL_2026-04-17_P_95",
            "option_type": "PUT",
            "strike": 95.0,
        },
        "net_credit": 1.0,
        "net_debit": 0.0,
        "width": 5.0,
        "selection_score": 0.2,
    }
    decision = {
        "symbol": "AAPL",
        "market_regime": "TREND_UP",
        "directional_state": "BULLISH_CONTINUATION",
        "iv_state": "IV_RICH",
    }

    idea = build_trade_idea(
        trade_candidate=trade_candidate,
        decision=decision,
    )

    assert idea["symbol"] == "AAPL"
    assert idea["strategy_family"] == "BULL_PUT_SPREAD"
    assert idea["expiration"] == "2026-04-17"
    assert idea["option_type"] == "PUT"
    assert idea["short_strike"] == 100.0
    assert idea["long_strike"] == 95.0
    assert idea["net_credit"] == 1.0
    assert idea["width"] == 5.0
    assert idea["max_risk"] == 4.0
    assert idea["score"] == 0.2
    assert idea["market_regime"] == "TREND_UP"
    assert idea["directional_state"] == "BULLISH_CONTINUATION"
    assert idea["iv_state"] == "IV_RICH"


def test_build_trade_ideas_matches_candidates_to_decisions() -> None:
    ideas = build_trade_ideas(
        trade_candidates=[
            {
                "symbol": "AAPL",
                "strategy_family": "BULL_PUT_SPREAD",
                "expiration": "2026-04-17",
                "short_leg": {
                    "option_symbol": "AAPL_2026-04-17_P_100",
                    "option_type": "PUT",
                    "strike": 100.0,
                },
                "long_leg": {
                    "option_symbol": "AAPL_2026-04-17_P_95",
                    "option_type": "PUT",
                    "strike": 95.0,
                },
                "net_credit": 1.0,
                "net_debit": 0.0,
                "width": 5.0,
                "selection_score": 0.2,
            }
        ],
        decisions=[
            {
                "symbol": "AAPL",
                "market_regime": "TREND_UP",
                "directional_state": "BULLISH_CONTINUATION",
                "iv_state": "IV_RICH",
            }
        ],
    )

    assert len(ideas) == 1
    assert ideas[0]["symbol"] == "AAPL"
