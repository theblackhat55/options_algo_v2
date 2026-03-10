from options_algo_v2.classifiers.directional_state import classify_directional_state
from options_algo_v2.domain.enums import DirectionalState
from options_algo_v2.domain.features import DirectionalFeatures


def test_classify_bullish_continuation() -> None:
    features = DirectionalFeatures(
        close_above_20dma=True,
        close_above_50dma=True,
        close_below_20dma=False,
        close_below_50dma=False,
        adx=22.0,
        rsi=58.0,
        five_day_return=2.5,
        breakout_above_20d_high=False,
        breakdown_below_20d_low=False,
        breakout_volume_multiple=1.1,
        extended_up=False,
        extended_down=False,
    )
    assert classify_directional_state(features) == DirectionalState.BULLISH_CONTINUATION


def test_classify_bullish_breakout() -> None:
    features = DirectionalFeatures(
        close_above_20dma=True,
        close_above_50dma=True,
        close_below_20dma=False,
        close_below_50dma=False,
        adx=20.0,
        rsi=60.0,
        five_day_return=3.0,
        breakout_above_20d_high=True,
        breakdown_below_20d_low=False,
        breakout_volume_multiple=1.8,
        extended_up=False,
        extended_down=False,
    )
    assert classify_directional_state(features) == DirectionalState.BULLISH_BREAKOUT


def test_classify_bearish_continuation() -> None:
    features = DirectionalFeatures(
        close_above_20dma=False,
        close_above_50dma=False,
        close_below_20dma=True,
        close_below_50dma=True,
        adx=21.0,
        rsi=42.0,
        five_day_return=-2.0,
        breakout_above_20d_high=False,
        breakdown_below_20d_low=False,
        breakout_volume_multiple=1.0,
        extended_up=False,
        extended_down=False,
    )
    assert classify_directional_state(features) == DirectionalState.BEARISH_CONTINUATION


def test_classify_bearish_breakdown() -> None:
    features = DirectionalFeatures(
        close_above_20dma=False,
        close_above_50dma=False,
        close_below_20dma=True,
        close_below_50dma=True,
        adx=19.0,
        rsi=38.0,
        five_day_return=-3.0,
        breakout_above_20d_high=False,
        breakdown_below_20d_low=True,
        breakout_volume_multiple=1.7,
        extended_up=False,
        extended_down=False,
    )
    assert classify_directional_state(features) == DirectionalState.BEARISH_BREAKDOWN


def test_classify_no_trade_when_extended() -> None:
    features = DirectionalFeatures(
        close_above_20dma=True,
        close_above_50dma=True,
        close_below_20dma=False,
        close_below_50dma=False,
        adx=25.0,
        rsi=65.0,
        five_day_return=4.0,
        breakout_above_20d_high=True,
        breakdown_below_20d_low=False,
        breakout_volume_multiple=2.0,
        extended_up=True,
        extended_down=False,
    )
    assert classify_directional_state(features) == DirectionalState.NO_TRADE


def test_classify_neutral() -> None:
    features = DirectionalFeatures(
        close_above_20dma=True,
        close_above_50dma=False,
        close_below_20dma=False,
        close_below_50dma=False,
        adx=12.0,
        rsi=50.0,
        five_day_return=0.1,
        breakout_above_20d_high=False,
        breakdown_below_20d_low=False,
        breakout_volume_multiple=1.0,
        extended_up=False,
        extended_down=False,
    )
    assert classify_directional_state(features) == DirectionalState.NEUTRAL
