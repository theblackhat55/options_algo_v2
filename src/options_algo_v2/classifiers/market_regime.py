from __future__ import annotations

from options_algo_v2.domain.enums import MarketRegime
from options_algo_v2.domain.features import MarketRegimeFeatures


def classify_market_regime(
    features: MarketRegimeFeatures,
    breadth_bullish_threshold: float = 52.0,
    breadth_bearish_threshold: float = 48.0,
) -> MarketRegime:
    if features.vix_defensive:
        return MarketRegime.RISK_OFF

    if (
        features.spy_close_above_20dma
        and features.spy_20dma_above_50dma
        and features.breadth_pct_above_20dma > breadth_bullish_threshold
    ):
        return MarketRegime.TREND_UP

    if (
        features.spy_close_below_20dma
        and features.spy_20dma_below_50dma
        and features.breadth_pct_above_20dma < breadth_bearish_threshold
    ):
        return MarketRegime.TREND_DOWN

    return MarketRegime.RANGE_UNCLEAR
