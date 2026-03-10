from options_algo_v2.domain.enums import DirectionalState
from options_algo_v2.services.extension_filter import passes_extension_filter


def test_extension_filter_passes_for_non_extended_bullish_setup() -> None:
    result = passes_extension_filter(
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        close=103.0,
        dma20=100.0,
        atr20=2.0,
    )

    assert result.passed is True


def test_extension_filter_rejects_extended_bullish_setup() -> None:
    result = passes_extension_filter(
        directional_state=DirectionalState.BULLISH_BREAKOUT,
        close=104.0,
        dma20=100.0,
        atr20=2.0,
    )

    assert result.passed is False
    assert "bullish setup is too extended above 20 dma" in result.reasons


def test_extension_filter_passes_for_non_extended_bearish_setup() -> None:
    result = passes_extension_filter(
        directional_state=DirectionalState.BEARISH_CONTINUATION,
        close=97.5,
        dma20=100.0,
        atr20=2.0,
    )

    assert result.passed is True


def test_extension_filter_rejects_extended_bearish_setup() -> None:
    result = passes_extension_filter(
        directional_state=DirectionalState.BEARISH_BREAKDOWN,
        close=96.0,
        dma20=100.0,
        atr20=2.0,
    )

    assert result.passed is False
    assert "bearish setup is too extended below 20 dma" in result.reasons


def test_extension_filter_rejects_negative_atr() -> None:
    result = passes_extension_filter(
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        close=100.0,
        dma20=100.0,
        atr20=-1.0,
    )

    assert result.passed is False
    assert "atr20 cannot be negative" in result.reasons
