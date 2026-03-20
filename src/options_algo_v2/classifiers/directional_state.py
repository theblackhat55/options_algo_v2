from __future__ import annotations

from options_algo_v2.domain.enums import DirectionalState
from options_algo_v2.domain.features import DirectionalFeatures


def classify_directional_state(
    features: DirectionalFeatures,
    adx_trending_min: float = 18.0,
    adx_breakout_min: float = 16.0,
    rsi_bullish_min: float = 45.0,
    rsi_bullish_max: float = 75.0,
    rsi_bearish_min: float = 25.0,
    rsi_bearish_max: float = 55.0,
    breakout_volume_multiple_min: float = 1.5,
) -> DirectionalState:
    if features.extended_up or features.extended_down:
        return DirectionalState.NO_TRADE

    if (
        features.close_above_20dma
        and features.close_above_50dma
        and features.adx >= adx_trending_min
        and rsi_bullish_min <= features.rsi <= rsi_bullish_max
    ):
        if (
            features.breakout_above_20d_high
            and features.breakout_volume_multiple >= breakout_volume_multiple_min
            and features.adx >= adx_breakout_min
        ):
            return DirectionalState.BULLISH_BREAKOUT
        return DirectionalState.BULLISH_CONTINUATION

    if (
        features.close_below_20dma
        and features.close_below_50dma
        and features.adx >= adx_trending_min
        and rsi_bearish_min <= features.rsi <= rsi_bearish_max
    ):
        if (
            features.breakdown_below_20d_low
            and features.breakout_volume_multiple >= breakout_volume_multiple_min
            and features.adx >= adx_breakout_min
        ):
            return DirectionalState.BEARISH_BREAKDOWN
        return DirectionalState.BEARISH_CONTINUATION

    return DirectionalState.NEUTRAL
