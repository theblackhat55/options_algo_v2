from options_algo_v2.domain.enums import (
    DirectionalState,
    IVState,
    MarketRegime,
    SignalState,
    StrategyType,
)
from options_algo_v2.services.strategy_selector import select_strategy_candidate


def test_selects_bull_put_spread_for_bullish_rich_iv() -> None:
    candidate = select_strategy_candidate(
        symbol="AAPL",
        market_regime=MarketRegime.TREND_UP,
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
    )

    assert candidate.strategy_type == StrategyType.BULL_PUT_SPREAD
    assert candidate.signal_state == SignalState.QUALIFIED


def test_selects_bull_call_spread_for_bullish_normal_iv() -> None:
    candidate = select_strategy_candidate(
        symbol="MSFT",
        market_regime=MarketRegime.TREND_UP,
        directional_state=DirectionalState.BULLISH_BREAKOUT,
        iv_state=IVState.IV_NORMAL,
    )

    assert candidate.strategy_type == StrategyType.BULL_CALL_SPREAD
    assert candidate.signal_state == SignalState.QUALIFIED


def test_selects_bear_call_spread_for_bearish_rich_iv() -> None:
    candidate = select_strategy_candidate(
        symbol="NVDA",
        market_regime=MarketRegime.TREND_DOWN,
        directional_state=DirectionalState.BEARISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
    )

    assert candidate.strategy_type == StrategyType.BEAR_CALL_SPREAD
    assert candidate.signal_state == SignalState.QUALIFIED


def test_selects_bear_put_spread_for_bearish_cheap_iv() -> None:
    candidate = select_strategy_candidate(
        symbol="TSLA",
        market_regime=MarketRegime.TREND_DOWN,
        directional_state=DirectionalState.BEARISH_BREAKDOWN,
        iv_state=IVState.IV_CHEAP,
    )

    assert candidate.strategy_type == StrategyType.BEAR_PUT_SPREAD
    assert candidate.signal_state == SignalState.QUALIFIED


def test_range_unclear_allows_defined_risk_spreads() -> None:
    # RANGE_UNCLEAR now permits defined-risk spreads (bull put, bear call, bear put)
    candidate = select_strategy_candidate(
        symbol="SPY",
        market_regime=MarketRegime.RANGE_UNCLEAR,
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
    )

    assert candidate.signal_state == SignalState.QUALIFIED
    assert candidate.strategy_type == StrategyType.BULL_PUT_SPREAD


def test_rejects_risk_off_regime_regardless_of_direction() -> None:
    # RISK_OFF still rejects all strategies
    candidate = select_strategy_candidate(
        symbol="SPY",
        market_regime=MarketRegime.RISK_OFF,
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
    )

    assert candidate.signal_state == SignalState.REJECTED
    assert candidate.rationale
    assert "market regime" in candidate.rationale[0]


def test_rejects_risk_off_regime() -> None:
    candidate = select_strategy_candidate(
        symbol="QQQ",
        market_regime=MarketRegime.RISK_OFF,
        directional_state=DirectionalState.BEARISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
    )

    assert candidate.signal_state == SignalState.REJECTED
    assert candidate.rationale
    assert "market regime" in candidate.rationale[0]


def test_rejects_neutral_directional_state() -> None:
    candidate = select_strategy_candidate(
        symbol="AMD",
        market_regime=MarketRegime.TREND_UP,
        directional_state=DirectionalState.NEUTRAL,
        iv_state=IVState.IV_NORMAL,
    )

    assert candidate.signal_state == SignalState.REJECTED
    assert candidate.rationale
    assert "directional state" in candidate.rationale[0]


def test_rejects_bullish_trade_in_trend_down_regime() -> None:
    candidate = select_strategy_candidate(
        symbol="META",
        market_regime=MarketRegime.TREND_DOWN,
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
    )

    assert candidate.signal_state == SignalState.REJECTED
    assert candidate.rationale
    assert "strategy not permitted" in candidate.rationale[0]
