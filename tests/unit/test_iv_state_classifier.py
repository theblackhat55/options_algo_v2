from options_algo_v2.classifiers.iv_state import classify_iv_state
from options_algo_v2.domain.enums import IVState
from options_algo_v2.domain.features import IVFeatures


def test_classify_iv_rich_from_rank_and_ratio() -> None:
    """IV_RICH now requires 2-of-3 signals. Rank alone is not enough."""
    features = IVFeatures(iv_rank=75.0, iv_hv_ratio=1.30, iv_rv_spread=2.0)
    assert classify_iv_state(features) == IVState.IV_RICH


def test_classify_iv_not_rich_from_single_signal() -> None:
    """Only iv_rank is rich (1-of-3) -> should be IV_NORMAL, not IV_RICH."""
    features = IVFeatures(iv_rank=75.0, iv_hv_ratio=1.10, iv_rv_spread=2.0)
    assert classify_iv_state(features) == IVState.IV_NORMAL


def test_classify_iv_rich_from_ratio_and_spread() -> None:
    features = IVFeatures(iv_rank=45.0, iv_hv_ratio=1.30, iv_rv_spread=6.0)
    assert classify_iv_state(features) == IVState.IV_RICH


def test_classify_iv_cheap() -> None:
    features = IVFeatures(iv_rank=25.0, iv_hv_ratio=1.00, iv_rv_spread=1.0)
    assert classify_iv_state(features) == IVState.IV_CHEAP


def test_classify_iv_normal() -> None:
    features = IVFeatures(iv_rank=45.0, iv_hv_ratio=1.10, iv_rv_spread=2.0)
    assert classify_iv_state(features) == IVState.IV_NORMAL


def test_classify_iv_rank_fallback() -> None:
    features = IVFeatures(iv_rank=None, iv_hv_ratio=1.10, iv_rv_spread=2.0)
    assert classify_iv_state(features) == IVState.IV_NORMAL
