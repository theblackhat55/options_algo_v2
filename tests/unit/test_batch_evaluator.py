from datetime import date

from options_algo_v2.domain.raw_features import RawFeatureInput
from options_algo_v2.services.batch_evaluator import evaluate_raw_feature_batch


def test_evaluate_raw_feature_batch_returns_decisions() -> None:
    raw_inputs = [
        RawFeatureInput(
            symbol="AAPL",
            close=105.0,
            dma20=100.0,
            dma50=95.0,
            atr20=2.0,
            adx14=22.0,
            iv_rank=70.0,
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
        ),
        RawFeatureInput(
            symbol="SPY",
            close=100.0,
            dma20=100.0,
            dma50=100.0,
            atr20=2.0,
            adx14=10.0,
            iv_rank=45.0,
            iv_hv_ratio=1.10,
            avg_daily_volume=10_000_000,
            option_open_interest=3_000,
            option_volume=800,
            bid=1.90,
            ask=2.00,
            option_quote_age_seconds=10,
            underlying_quote_age_seconds=2,
            market_breadth_pct_above_20dma=50.0,
            earnings_date=None,
            entry_date=date(2026, 3, 10),
            dte_days=20,
        ),
    ]

    decisions = evaluate_raw_feature_batch(raw_inputs)

    assert len(decisions) == 2
    assert decisions[0].candidate.symbol == "AAPL"
    assert decisions[1].candidate.symbol == "SPY"
