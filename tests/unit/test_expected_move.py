from options_algo_v2.services.expected_move import (
    compare_expected_moves,
    compute_forecast_move,
    compute_implied_expected_move,
)


def test_compute_implied_expected_move() -> None:
    # 30% IV, 30 DTE -> 0.30 * sqrt(30/365) * 100 ~= 8.6%
    move = compute_implied_expected_move(atm_iv=0.30, dte_days=30)
    assert 8.0 < move < 10.0


def test_compute_implied_expected_move_zero_inputs() -> None:
    assert compute_implied_expected_move(atm_iv=0.0, dte_days=30) == 0.0
    assert compute_implied_expected_move(atm_iv=0.3, dte_days=0) == 0.0


def test_compute_forecast_move() -> None:
    # ATR20=3.0, close=100, DTE=30
    # daily_vol_pct = 3/100 * 100 = 3.0
    # forecast = 3.0 * sqrt(30) ~= 16.4
    move = compute_forecast_move(atr20=3.0, close=100.0, dte_days=30)
    assert 16.0 < move < 17.0


def test_compare_expected_moves_sell_premium() -> None:
    # High IV relative to realized -> sell premium
    # implied: 0.50 * sqrt(30/365) * 100 ~= 14.3%
    # forecast: 1.0/100 * 100 * sqrt(30) ~= 5.5%  -> ratio ~2.6
    result = compare_expected_moves(
        atm_iv=0.50,
        dte_days=30,
        atr20=1.0,
        close=100.0,
    )
    assert result.edge == "sell_premium"
    assert result.ratio > 1.15


def test_compare_expected_moves_buy_premium() -> None:
    # Low IV relative to realized -> buy premium
    # implied: 0.05 * sqrt(30/365) * 100 ~= 1.4%
    # forecast: 5.0/100 * 100 * sqrt(30) ~= 27.4%  -> ratio ~0.05
    result = compare_expected_moves(
        atm_iv=0.05,
        dte_days=30,
        atr20=5.0,
        close=100.0,
    )
    assert result.edge == "buy_premium"
    assert result.ratio < 0.85


def test_compare_expected_moves_neutral() -> None:
    # implied: 0.25 * sqrt(30/365) * 100 ~= 7.2%
    # forecast: 2.5/100 * 100 * sqrt(30) ~= 13.7%  -> ratio ~0.52
    # That's actually buy_premium. Let's use values that produce ~1.0 ratio.
    # implied: 0.38 * sqrt(30/365) * 100 ~= 10.9%
    # forecast: 2.0/100 * 100 * sqrt(30) ~= 10.95%  -> ratio ~1.0
    result = compare_expected_moves(
        atm_iv=0.38,
        dte_days=30,
        atr20=2.0,
        close=100.0,
    )
    assert result.edge == "neutral"
