from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.domain.enums import MarketRegime


@dataclass(frozen=True)
class RegimeTransition:
    previous: MarketRegime
    current: MarketRegime
    is_transition: bool
    is_improving: bool  # moving toward TREND_UP from worse regimes
    is_degrading: bool  # moving toward RISK_OFF from better regimes
    days_in_current: int

    @property
    def confidence(self) -> float:
        """Confidence in the current regime (0-1). Lower during transitions."""
        if not self.is_transition:
            # Longer in same regime = higher confidence, max at 10+ days
            return min(1.0, self.days_in_current / 10.0)
        # Recent transition = lower confidence
        return max(0.2, min(0.6, self.days_in_current / 5.0))


# Regime ordering from most bullish to most bearish
_REGIME_RANK = {
    MarketRegime.TREND_UP: 4,
    MarketRegime.RANGE_UNCLEAR: 2,
    MarketRegime.TREND_DOWN: 1,
    MarketRegime.RISK_OFF: 0,
    MarketRegime.SYSTEM_DEGRADED: -1,
}


def detect_regime_transition(
    regime_history: list[MarketRegime],
    *,
    transition_lookback: int = 5,
) -> RegimeTransition:
    """Detect whether the market regime is in transition.

    Looks at recent regime history to determine if we've recently
    changed regimes and whether conditions are improving or degrading.
    """
    if not regime_history:
        return RegimeTransition(
            previous=MarketRegime.RANGE_UNCLEAR,
            current=MarketRegime.RANGE_UNCLEAR,
            is_transition=False,
            is_improving=False,
            is_degrading=False,
            days_in_current=0,
        )

    current = regime_history[-1]

    # Count consecutive days in current regime
    days_in_current = 1
    for regime in reversed(regime_history[:-1]):
        if regime == current:
            days_in_current += 1
        else:
            break

    # Find previous regime (last different regime)
    previous = current
    for regime in reversed(regime_history[:-1]):
        if regime != current:
            previous = regime
            break

    is_transition = days_in_current <= transition_lookback and previous != current
    current_rank = _REGIME_RANK.get(current, 2)
    previous_rank = _REGIME_RANK.get(previous, 2)

    return RegimeTransition(
        previous=previous,
        current=current,
        is_transition=is_transition,
        is_improving=current_rank > previous_rank,
        is_degrading=current_rank < previous_rank,
        days_in_current=days_in_current,
    )
