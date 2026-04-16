from __future__ import annotations

from options_algo_v2.domain.candidates import StrategyCandidate
from options_algo_v2.domain.enums import (
    DirectionalState,
    IVState,
    MarketRegime,
    SignalState,
    StrategyType,
)
from options_algo_v2.services.rulebook_policy import regime_allows_strategy
from options_algo_v2.services.strategy_eligibility import eligible_directional_strategies


def _reject_candidate(
    *,
    symbol: str,
    market_regime: MarketRegime,
    directional_state: DirectionalState,
    iv_state: IVState,
    reason: str,
    strategy_type: StrategyType | None = None,
) -> StrategyCandidate:
    return StrategyCandidate(
        symbol=symbol,
        market_regime=market_regime,
        directional_state=directional_state,
        iv_state=iv_state,
        strategy_type=strategy_type or StrategyType.BULL_CALL_SPREAD,
        signal_state=SignalState.REJECTED,
        score=0.0,
        rationale=[reason],
    )


def select_strategy_candidate(
    *,
    symbol: str,
    market_regime: MarketRegime,
    directional_state: DirectionalState,
    iv_state: IVState,
    expected_move_fit: bool = False,
) -> StrategyCandidate:
    if market_regime in {
        MarketRegime.RISK_OFF,
        MarketRegime.SYSTEM_DEGRADED,
    }:
        return _reject_candidate(
            symbol=symbol,
            market_regime=market_regime,
            directional_state=directional_state,
            iv_state=iv_state,
            reason="market regime does not permit new entries",
        )

    if directional_state in {
        DirectionalState.NEUTRAL,
        DirectionalState.NO_TRADE,
    }:
        return _reject_candidate(
            symbol=symbol,
            market_regime=market_regime,
            directional_state=directional_state,
            iv_state=iv_state,
            reason="directional state is not actionable",
        )

    strategy_type: StrategyType

    eligible_strategies = eligible_directional_strategies(
        directional_state=directional_state,
        iv_state=iv_state,
        expected_move_1d_pct=4.0 if expected_move_fit else 1.0,
    )

    if directional_state in {
        DirectionalState.BULLISH_CONTINUATION,
        DirectionalState.BULLISH_BREAKOUT,
    }:
        if iv_state == IVState.IV_RICH:
            strategy_type = StrategyType.BULL_PUT_SPREAD
        else:
            strategy_type = StrategyType.BULL_CALL_SPREAD
    elif directional_state in {
        DirectionalState.BEARISH_CONTINUATION,
        DirectionalState.BEARISH_BREAKDOWN,
    }:
        if iv_state == IVState.IV_RICH:
            strategy_type = StrategyType.BEAR_CALL_SPREAD
        else:
            strategy_type = StrategyType.BEAR_PUT_SPREAD
    else:
        return _reject_candidate(
            symbol=symbol,
            market_regime=market_regime,
            directional_state=directional_state,
            iv_state=iv_state,
            reason="unhandled directional state",
        )

    if not regime_allows_strategy(market_regime, strategy_type):
        return _reject_candidate(
            symbol=symbol,
            market_regime=market_regime,
            directional_state=directional_state,
            iv_state=iv_state,
            reason="strategy not permitted in current regime",
            strategy_type=strategy_type,
        )

    rationale = [
        f"market_regime={market_regime.value}",
        f"directional_state={directional_state.value}",
        f"iv_state={iv_state.value}",
        f"selected_strategy={strategy_type.value}",
        "eligible_strategies=" + ",".join(s.value for s in eligible_strategies),
    ]

    if StrategyType.LONG_CALL in eligible_strategies:
        rationale.append("long_call_alternative_eligible")

    if StrategyType.LONG_PUT in eligible_strategies:
        rationale.append("long_put_alternative_eligible")

    if market_regime == MarketRegime.RANGE_UNCLEAR:
        rationale.append("range_unclear_allowed_for_defined_risk_spread")

    return StrategyCandidate(
        symbol=symbol,
        market_regime=market_regime,
        directional_state=directional_state,
        iv_state=iv_state,
        strategy_type=strategy_type,
        signal_state=SignalState.QUALIFIED,
        score=0.0,
        rationale=rationale,
    )
