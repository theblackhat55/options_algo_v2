from __future__ import annotations

from options_algo_v2.domain.enums import DirectionalState, IVState, StrategyType


def eligible_directional_strategies(
    *,
    directional_state: str,
    iv_state: str,
    expected_move_1d_pct: float | None,
) -> list[StrategyType]:
    strategies: list[StrategyType] = []

    bullish = directional_state in {
        DirectionalState.BULLISH_CONTINUATION,
        DirectionalState.BULLISH_BREAKOUT,
    }
    bearish = directional_state in {
        DirectionalState.BEARISH_CONTINUATION,
        DirectionalState.BEARISH_BREAKDOWN,
    }

    iv_ok_for_long_premium = iv_state in {
        IVState.IV_NORMAL,
        IVState.IV_CHEAP,
    }

    strong_move = expected_move_1d_pct is not None and expected_move_1d_pct >= 3.5

    if bullish:
        strategies.append(StrategyType.BULL_CALL_SPREAD)
        if iv_ok_for_long_premium and strong_move:
            strategies.append(StrategyType.LONG_CALL)

    if bearish:
        strategies.append(StrategyType.BEAR_PUT_SPREAD)
        if iv_ok_for_long_premium and strong_move:
            strategies.append(StrategyType.LONG_PUT)

    return strategies
