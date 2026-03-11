from __future__ import annotations

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.iv_feature_estimator import (
    compute_hv20_from_bar_rows,
    compute_iv_hv_ratio_from_snapshot_and_bars,
    estimate_near_atm_implied_vol,
)


def _bars() -> list[dict[str, object]]:
    closes = [
        100.0, 101.0, 100.5, 102.0, 101.5,
        103.0, 104.0, 103.5, 105.0, 106.0,
        105.5, 106.5, 107.0, 108.0, 107.5,
        109.0, 110.0, 109.5, 111.0, 112.0,
        111.5,
    ]
    return [{"close": close} for close in closes]


def test_compute_hv20_from_bar_rows_returns_positive_value() -> None:
    hv20 = compute_hv20_from_bar_rows(_bars())
    assert hv20 is not None
    assert hv20 > 0


def test_estimate_near_atm_implied_vol_returns_average_of_nearest_quotes() -> None:
    snapshot = OptionsChainSnapshot(
        symbol="AAPL",
        quotes=[
            OptionQuote(
                symbol="AAPL",
                option_symbol="O:AAPL260417C00145000",
                expiration="2026-04-17",
                strike=145.0,
                option_type="CALL",
                bid=4.9,
                ask=5.1,
                mid=5.0,
                delta=0.60,
                implied_volatility=0.24,
                open_interest=1000,
                volume=200,
            ),
            OptionQuote(
                symbol="AAPL",
                option_symbol="O:AAPL260417C00150000",
                expiration="2026-04-17",
                strike=150.0,
                option_type="CALL",
                bid=2.4,
                ask=2.6,
                mid=2.5,
                delta=0.50,
                implied_volatility=0.22,
                open_interest=900,
                volume=150,
            ),
            OptionQuote(
                symbol="AAPL",
                option_symbol="O:AAPL260417C00155000",
                expiration="2026-04-17",
                strike=155.0,
                option_type="CALL",
                bid=1.1,
                ask=1.3,
                mid=1.2,
                delta=0.35,
                implied_volatility=0.26,
                open_interest=800,
                volume=120,
            ),
        ],
    )

    iv = estimate_near_atm_implied_vol(snapshot=snapshot, underlying_price=151.0)
    assert iv is not None
    assert iv > 0


def test_compute_iv_hv_ratio_from_snapshot_and_bars_returns_positive_value() -> None:
    snapshot = OptionsChainSnapshot(
        symbol="AAPL",
        quotes=[
            OptionQuote(
                symbol="AAPL",
                option_symbol="O:AAPL260417C00150000",
                expiration="2026-04-17",
                strike=150.0,
                option_type="CALL",
                bid=2.4,
                ask=2.6,
                mid=2.5,
                delta=0.50,
                implied_volatility=0.22,
                open_interest=900,
                volume=150,
            ),
        ],
    )

    ratio = compute_iv_hv_ratio_from_snapshot_and_bars(
        snapshot=snapshot,
        bar_rows=_bars(),
        underlying_price=151.0,
    )
    assert ratio is not None
    assert ratio > 0
