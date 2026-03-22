import pytest

from options_algo_v2.services.top_trade_summary_builder import (
    build_top_trade_summary_rows,
)


def test_build_top_trade_summary_rows_returns_expected_shape() -> None:
    candidates = [
        {
            "symbol": "AAPL",
            "strategy_family": "BULL_PUT_SPREAD",
            "expiration": "2026-04-17",
            "net_credit": 1.0,
            "width": 5.0,
        },
        {
            "symbol": "MSFT",
            "strategy_family": "BULL_PUT_SPREAD",
            "expiration": "2026-04-17",
            "net_credit": 2.0,
            "width": 5.0,
        },
    ]

    rows = build_top_trade_summary_rows(candidates)

    assert len(rows) == 2
    assert rows[0]["symbol"] == "AAPL"
    assert rows[0]["strategy_family"] == "BULL_PUT_SPREAD"
    assert rows[0]["expiration"] == "2026-04-17"
    assert rows[0]["net_credit"] == 1.0
    assert rows[0]["width"] == 5.0
    # score = net_credit/width + options_context_adjustment
    # options_context_adjustment: confidence=0.0 < 0.50 → -0.25
    # AAPL: 1.0/5.0 - 0.25 = -0.05
    # MSFT: 2.0/5.0 - 0.25 = 0.15
    assert rows[0]["score"] == pytest.approx(-0.05, abs=1e-9)
    assert rows[1]["score"] == pytest.approx(0.15, abs=1e-9)
