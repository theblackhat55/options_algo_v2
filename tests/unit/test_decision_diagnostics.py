from options_algo_v2.domain.candidates import StrategyCandidate
from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.enums import (
    DirectionalState,
    IVState,
    MarketRegime,
    SignalState,
    StrategyType,
)
from options_algo_v2.domain.qualification import QualificationResult
from options_algo_v2.services.decision_diagnostics import (
    count_rejection_reasons,
    count_signal_states,
    count_strategy_types,
)


def _make_decision(
    *,
    symbol: str,
    strategy_type: StrategyType,
    signal_state: SignalState,
    final_passed: bool,
    rejection_reasons: list[str],
) -> CandidateDecision:
    candidate = StrategyCandidate(
        symbol=symbol,
        market_regime=MarketRegime.TREND_UP,
        directional_state=DirectionalState.BULLISH_CONTINUATION,
        iv_state=IVState.IV_RICH,
        strategy_type=strategy_type,
        signal_state=signal_state,
        score=85.0,
        rationale="test rationale",
    )

    passed_result = QualificationResult(passed=True, reasons=[])
    failed_result = QualificationResult(passed=False, reasons=["failed"])

    return CandidateDecision(
        candidate=candidate,
        event_result=passed_result,
        liquidity_result=passed_result,
        extension_result=failed_result if not final_passed else passed_result,
        final_passed=final_passed,
        final_score=85.0 if final_passed else 40.0,
        min_score_required=70.0,
        rejection_reasons=rejection_reasons,
    )


def test_count_rejection_reasons_aggregates_all_reasons() -> None:
    decisions = [
        _make_decision(
            symbol="AAPL",
            strategy_type=StrategyType.BULL_PUT_SPREAD,
            signal_state=SignalState.REJECTED,
            final_passed=False,
            rejection_reasons=["liquidity_failed", "below_min_score"],
        ),
        _make_decision(
            symbol="MSFT",
            strategy_type=StrategyType.BULL_CALL_SPREAD,
            signal_state=SignalState.REJECTED,
            final_passed=False,
            rejection_reasons=["liquidity_failed"],
        ),
    ]

    assert count_rejection_reasons(decisions) == {
        "below_min_score": 1,
        "liquidity_failed": 2,
    }


def test_count_signal_states_returns_counts() -> None:
    decisions = [
        _make_decision(
            symbol="AAPL",
            strategy_type=StrategyType.BULL_PUT_SPREAD,
            signal_state=SignalState.QUALIFIED,
            final_passed=True,
            rejection_reasons=[],
        ),
        _make_decision(
            symbol="MSFT",
            strategy_type=StrategyType.BULL_CALL_SPREAD,
            signal_state=SignalState.REJECTED,
            final_passed=False,
            rejection_reasons=["extension_failed"],
        ),
    ]

    assert count_signal_states(decisions) == {
        SignalState.QUALIFIED.value: 1,
        SignalState.REJECTED.value: 1,
    }


def test_count_strategy_types_returns_counts() -> None:
    decisions = [
        _make_decision(
            symbol="AAPL",
            strategy_type=StrategyType.BULL_PUT_SPREAD,
            signal_state=SignalState.QUALIFIED,
            final_passed=True,
            rejection_reasons=[],
        ),
        _make_decision(
            symbol="MSFT",
            strategy_type=StrategyType.BULL_PUT_SPREAD,
            signal_state=SignalState.REJECTED,
            final_passed=False,
            rejection_reasons=["below_min_score"],
        ),
        _make_decision(
            symbol="SPY",
            strategy_type=StrategyType.BEAR_PUT_SPREAD,
            signal_state=SignalState.REJECTED,
            final_passed=False,
            rejection_reasons=["selector_rejected"],
        ),
    ]

    assert count_strategy_types(decisions) == {
        StrategyType.BEAR_PUT_SPREAD.value: 1,
        StrategyType.BULL_PUT_SPREAD.value: 2,
    }
