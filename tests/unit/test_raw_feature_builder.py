from datetime import date

from options_algo_v2.domain.computed_features import ComputedUnderlyingFeatures
from options_algo_v2.services.raw_feature_builder import build_raw_feature_input


def test_build_raw_feature_input_returns_expected_model() -> None:
    computed = ComputedUnderlyingFeatures(
        close=150.0,
        dma20=148.0,
        dma50=140.0,
        atr20=3.5,
    )

    raw = build_raw_feature_input(
        symbol="AAPL",
        computed_features=computed,
        adx14=22.0,
        iv_rank=65.0,
        iv_hv_ratio=1.30,
        avg_daily_volume=5_000_000,
        option_open_interest=2_000,
        option_volume=400,
        bid=2.45,
        ask=2.55,
        option_quote_age_seconds=10,
        underlying_quote_age_seconds=2,
        market_breadth_pct_above_20dma=60.0,
        earnings_date=None,
        entry_date=date(2026, 3, 10),
        dte_days=35,
    )

    assert raw.symbol == "AAPL"
    assert raw.close == 150.0
    assert raw.dma20 == 148.0
    assert raw.dma50 == 140.0
    assert raw.atr20 == 3.5
    assert raw.adx14 == 22.0
    assert raw.iv_rank == 65.0
    assert raw.iv_hv_ratio == 1.30
    assert raw.avg_daily_volume == 5_000_000
    assert raw.option_open_interest == 2_000
    assert raw.option_volume == 400
    assert raw.bid == 2.45
    assert raw.ask == 2.55
    assert raw.option_quote_age_seconds == 10
    assert raw.underlying_quote_age_seconds == 2
    assert raw.market_breadth_pct_above_20dma == 60.0
    assert raw.earnings_date is None
    assert raw.entry_date == date(2026, 3, 10)
    assert raw.dte_days == 35
