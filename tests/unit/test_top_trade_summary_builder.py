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
    assert rows[0]["score"] == 0.2
    assert rows[1]["score"] == 0.4
