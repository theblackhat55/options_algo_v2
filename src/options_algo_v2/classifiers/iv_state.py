from __future__ import annotations

from options_algo_v2.domain.enums import IVState
from options_algo_v2.domain.features import IVFeatures


def classify_iv_state(
    features: IVFeatures,
    iv_rich_rank_min: float = 60.0,
    iv_cheap_rank_max: float = 30.0,
    iv_hv_rich_min: float = 1.25,
    iv_hv_cheap_max: float = 1.05,
    iv_rv_spread_rich_min: float = 5.0,
    iv_rank_fallback_value: float = 50.0,
) -> IVState:
    iv_rank = features.iv_rank if features.iv_rank is not None else iv_rank_fallback_value
    iv_hv_ratio = features.iv_hv_ratio
    iv_rv_spread = features.iv_rv_spread

    rich_signals = 0
    cheap_signals = 0

    if iv_rank >= iv_rich_rank_min:
        rich_signals += 1
    if iv_rank <= iv_cheap_rank_max:
        cheap_signals += 1

    if iv_hv_ratio is not None:
        if iv_hv_ratio >= iv_hv_rich_min:
            rich_signals += 1
        if iv_hv_ratio <= iv_hv_cheap_max:
            cheap_signals += 1

    if iv_rv_spread is not None and iv_rv_spread >= iv_rv_spread_rich_min:
        rich_signals += 1

    if rich_signals >= 1:
        return IVState.IV_RICH

    if cheap_signals >= 2:
        return IVState.IV_CHEAP

    return IVState.IV_NORMAL
