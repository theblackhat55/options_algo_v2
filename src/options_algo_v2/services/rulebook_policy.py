from __future__ import annotations

from datetime import date, timedelta

from options_algo_v2.domain.enums import MarketRegime, StrategyType


def regime_allows_strategy(
    regime: MarketRegime,
    strategy_type: StrategyType,
) -> bool:
    if regime in {
        MarketRegime.RISK_OFF,
        MarketRegime.SYSTEM_DEGRADED,
    }:
        return False

    if regime == MarketRegime.RANGE_UNCLEAR:
        return strategy_type in {
            StrategyType.BULL_PUT_SPREAD,
            StrategyType.BEAR_CALL_SPREAD,
            StrategyType.BEAR_PUT_SPREAD,
        }

    if regime == MarketRegime.TREND_UP:
        return strategy_type in {
            StrategyType.BULL_PUT_SPREAD,
            StrategyType.BULL_CALL_SPREAD,
        }

    if regime == MarketRegime.TREND_DOWN:
        return strategy_type in {
            StrategyType.BEAR_CALL_SPREAD,
            StrategyType.BEAR_PUT_SPREAD,
        }

    return False


def planned_latest_exit_date(
    entry_date: date,
    expiry_date: date,
    strategy_type: StrategyType,
) -> date:
    if strategy_type in {
        StrategyType.BULL_PUT_SPREAD,
        StrategyType.BEAR_CALL_SPREAD,
    }:
        expiry_buffer_exit = expiry_date - timedelta(days=7)
        max_holding_exit = entry_date + timedelta(days=21)
        return min(expiry_buffer_exit, max_holding_exit)

    if strategy_type in {
        StrategyType.BULL_CALL_SPREAD,
        StrategyType.BEAR_PUT_SPREAD,
    }:
        expiry_buffer_exit = expiry_date - timedelta(days=10)
        max_holding_exit = entry_date + timedelta(days=14)
        return min(expiry_buffer_exit, max_holding_exit)

    raise ValueError(f"Unsupported strategy type: {strategy_type}")


def earnings_within_holding_window(
    entry_date: date,
    expiry_date: date,
    earnings_date: date | None,
    strategy_type: StrategyType,
) -> bool:
    if earnings_date is None:
        return False

    latest_exit = planned_latest_exit_date(entry_date, expiry_date, strategy_type)
    return entry_date <= earnings_date <= latest_exit


def width_cap_for_underlying_price(price: float) -> float:
    if 20 <= price < 50:
        return 2.5
    if 50 <= price < 150:
        return 5.0
    if price >= 150:
        return 5.0
    raise ValueError("Underlying price below minimum supported threshold")
