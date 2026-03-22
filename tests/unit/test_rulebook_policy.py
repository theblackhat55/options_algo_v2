from datetime import date

from options_algo_v2.domain.enums import MarketRegime, StrategyType
from options_algo_v2.services.rulebook_policy import (
    earnings_within_holding_window,
    planned_latest_exit_date,
    regime_allows_strategy,
    width_cap_for_underlying_price,
)


def test_trend_up_allows_only_bullish_structures() -> None:
    assert regime_allows_strategy(
        MarketRegime.TREND_UP,
        StrategyType.BULL_PUT_SPREAD,
    ) is True
    assert regime_allows_strategy(
        MarketRegime.TREND_UP,
        StrategyType.BULL_CALL_SPREAD,
    ) is True
    assert regime_allows_strategy(
        MarketRegime.TREND_UP,
        StrategyType.BEAR_CALL_SPREAD,
    ) is False
    assert regime_allows_strategy(
        MarketRegime.TREND_UP,
        StrategyType.BEAR_PUT_SPREAD,
    ) is False


def test_trend_down_allows_only_bearish_structures() -> None:
    assert regime_allows_strategy(
        MarketRegime.TREND_DOWN,
        StrategyType.BEAR_CALL_SPREAD,
    ) is True
    assert regime_allows_strategy(
        MarketRegime.TREND_DOWN,
        StrategyType.BEAR_PUT_SPREAD,
    ) is True
    assert regime_allows_strategy(
        MarketRegime.TREND_DOWN,
        StrategyType.BULL_PUT_SPREAD,
    ) is False
    assert regime_allows_strategy(
        MarketRegime.TREND_DOWN,
        StrategyType.BULL_CALL_SPREAD,
    ) is False


def test_range_unclear_allows_defined_risk_spreads() -> None:
    # RANGE_UNCLEAR permits defined-risk credit/debit spreads
    assert regime_allows_strategy(
        MarketRegime.RANGE_UNCLEAR,
        StrategyType.BULL_PUT_SPREAD,
    ) is True
    assert regime_allows_strategy(
        MarketRegime.RANGE_UNCLEAR,
        StrategyType.BEAR_CALL_SPREAD,
    ) is True
    assert regime_allows_strategy(
        MarketRegime.RANGE_UNCLEAR,
        StrategyType.BEAR_PUT_SPREAD,
    ) is True
    # Pure long-bias debit spreads are not allowed in RANGE_UNCLEAR
    assert regime_allows_strategy(
        MarketRegime.RANGE_UNCLEAR,
        StrategyType.BULL_CALL_SPREAD,
    ) is False


def test_system_degraded_allows_no_new_entries() -> None:
    assert regime_allows_strategy(
        MarketRegime.SYSTEM_DEGRADED,
        StrategyType.BULL_CALL_SPREAD,
    ) is False
    assert regime_allows_strategy(
        MarketRegime.SYSTEM_DEGRADED,
        StrategyType.BEAR_PUT_SPREAD,
    ) is False


def test_credit_spread_planned_latest_exit_is_deterministic() -> None:
    entry = date(2026, 3, 10)
    expiry = date(2026, 4, 17)
    latest = planned_latest_exit_date(
        entry,
        expiry,
        StrategyType.BULL_PUT_SPREAD,
    )
    assert latest == date(2026, 3, 31)


def test_debit_spread_planned_latest_exit_is_deterministic() -> None:
    entry = date(2026, 3, 10)
    expiry = date(2026, 4, 17)
    latest = planned_latest_exit_date(
        entry,
        expiry,
        StrategyType.BULL_CALL_SPREAD,
    )
    assert latest == date(2026, 3, 24)


def test_earnings_inside_credit_holding_window_rejects_trade() -> None:
    entry = date(2026, 3, 10)
    expiry = date(2026, 4, 17)
    earnings = date(2026, 3, 25)
    assert earnings_within_holding_window(
        entry,
        expiry,
        earnings,
        StrategyType.BULL_PUT_SPREAD,
    ) is True


def test_earnings_outside_credit_holding_window_does_not_reject_trade() -> None:
    entry = date(2026, 3, 10)
    expiry = date(2026, 4, 17)
    earnings = date(2026, 4, 10)
    assert earnings_within_holding_window(
        entry,
        expiry,
        earnings,
        StrategyType.BULL_PUT_SPREAD,
    ) is False


def test_width_cap_under_50() -> None:
    assert width_cap_for_underlying_price(35.0) == 2.5


def test_width_cap_mid_tier() -> None:
    assert width_cap_for_underlying_price(100.0) == 5.0


def test_width_cap_high_tier() -> None:
    assert width_cap_for_underlying_price(250.0) == 5.0
