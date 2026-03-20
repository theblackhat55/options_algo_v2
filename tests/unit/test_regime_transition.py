from options_algo_v2.domain.enums import MarketRegime
from options_algo_v2.services.regime_transition import detect_regime_transition


def test_detect_no_transition_stable_regime() -> None:
    history = [MarketRegime.TREND_UP] * 10
    result = detect_regime_transition(history)
    assert result.is_transition is False
    assert result.current == MarketRegime.TREND_UP
    assert result.days_in_current == 10
    assert result.confidence == 1.0


def test_detect_recent_transition() -> None:
    history = [MarketRegime.RANGE_UNCLEAR] * 8 + [MarketRegime.TREND_UP] * 2
    result = detect_regime_transition(history)
    assert result.is_transition is True
    assert result.current == MarketRegime.TREND_UP
    assert result.previous == MarketRegime.RANGE_UNCLEAR
    assert result.is_improving is True
    assert result.is_degrading is False
    assert result.days_in_current == 2


def test_detect_degrading_transition() -> None:
    history = [MarketRegime.TREND_UP] * 8 + [MarketRegime.RISK_OFF] * 3
    result = detect_regime_transition(history)
    assert result.is_transition is True
    assert result.is_degrading is True
    assert result.is_improving is False


def test_detect_stable_after_transition_window() -> None:
    """After 6+ days in same regime, no longer a transition."""
    history = [MarketRegime.RANGE_UNCLEAR] * 5 + [MarketRegime.TREND_UP] * 6
    result = detect_regime_transition(history, transition_lookback=5)
    assert result.is_transition is False
    assert result.days_in_current == 6


def test_empty_history() -> None:
    result = detect_regime_transition([])
    assert result.current == MarketRegime.RANGE_UNCLEAR
    assert result.is_transition is False
    assert result.days_in_current == 0
