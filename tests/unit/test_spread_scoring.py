from __future__ import annotations

from options_algo_v2.services.spread_scoring import (
    score_bull_call_spread,
    score_bull_put_spread,
)


def test_score_bull_call_spread_returns_breakdown() -> None:
    score = score_bull_call_spread(
        long_leg_delta=0.34,
        long_leg_open_interest=1800,
        net_debit=1.5,
        width=5.0,
    )

    assert set(score.keys()) == {"delta_fit", "liquidity", "efficiency", "total"}
    assert 0.0 <= score["total"] <= 1.0
    assert score["delta_fit"] > 0.9


def test_score_bull_put_spread_returns_breakdown() -> None:
    score = score_bull_put_spread(
        short_leg_delta=-0.27,
        short_leg_open_interest=1700,
        net_credit=1.2,
        width=5.0,
    )

    assert set(score.keys()) == {"delta_fit", "liquidity", "efficiency", "total"}
    assert 0.0 <= score["total"] <= 1.0
    assert score["delta_fit"] > 0.9
