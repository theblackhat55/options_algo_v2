from __future__ import annotations

from options_algo_v2.domain.enums import DirectionalState
from options_algo_v2.domain.qualification import QualificationResult


def passes_extension_filter(
    *,
    directional_state: DirectionalState,
    close: float,
    dma20: float,
    atr20: float,
    extension_atr_multiple: float,
) -> QualificationResult:
    if atr20 < 0:
        return QualificationResult(
            passed=False,
            reasons=["atr20 cannot be negative"],
        )

    upper_limit = dma20 + (extension_atr_multiple * atr20)
    lower_limit = dma20 - (extension_atr_multiple * atr20)

    if directional_state in {
        DirectionalState.BULLISH_CONTINUATION,
        DirectionalState.BULLISH_BREAKOUT,
    } and close > upper_limit:
        return QualificationResult(
            passed=False,
            reasons=["bullish setup is too extended above 20 dma"],
        )

    if directional_state in {
        DirectionalState.BEARISH_CONTINUATION,
        DirectionalState.BEARISH_BREAKDOWN,
    } and close < lower_limit:
        return QualificationResult(
            passed=False,
            reasons=["bearish setup is too extended below 20 dma"],
        )

    return QualificationResult(passed=True, reasons=[])
