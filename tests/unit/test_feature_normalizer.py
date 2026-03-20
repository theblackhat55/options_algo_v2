from datetime import date

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.raw_features import RawFeatureInput
from options_algo_v2.services.feature_normalizer import (
    normalize_raw_features_to_payload,
)


def test_normalize_raw_features_to_bullish_rich_iv_payload() -> None:
    """Close is within 1.5 ATR of 20dma — not extended, bullish continuation."""
    raw = RawFeatureInput(
        symbol="AAPL",
        close=102.0,
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
    )

    payload = normalize_raw_features_to_payload(raw)

    assert payload.symbol == "AAPL"
    assert payload.market_regime == MarketRegime.TREND_UP
    assert payload.directional_state == DirectionalState.BULLISH_CONTINUATION
    assert payload.iv_state == IVState.IV_RICH
    assert payload.expected_move_fit is True


def test_normalize_extended_bullish_to_no_trade() -> None:
    """Close is > 1.5 ATR above 20dma — classified as extended → NO_TRADE."""
    raw = RawFeatureInput(
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
    )

    payload = normalize_raw_features_to_payload(raw)

    assert payload.directional_state == DirectionalState.NO_TRADE
    assert payload.expected_move_fit is False


def test_normalize_raw_features_to_neutral_normal_iv_payload() -> None:
    raw = RawFeatureInput(
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
    )

    payload = normalize_raw_features_to_payload(raw)

    assert payload.market_regime == MarketRegime.RANGE_UNCLEAR
    assert payload.directional_state == DirectionalState.NEUTRAL
    assert payload.iv_state == IVState.IV_NORMAL
