from __future__ import annotations

from datetime import date

from options_algo_v2.domain.enums import DirectionalState, IVState, MarketRegime
from options_algo_v2.domain.evaluation_input import CandidateEvaluationInput
from options_algo_v2.services.decision_engine import evaluate_candidate_decision
from options_algo_v2.services.scan_artifact_orchestrator import (
    build_and_write_scan_artifact,
)


def build_sample_decisions():
    inputs = [
        CandidateEvaluationInput(
            symbol="AAPL",
            market_regime=MarketRegime.TREND_UP,
            directional_state=DirectionalState.BULLISH_CONTINUATION,
            iv_state=IVState.IV_RICH,
            earnings_date=None,
            planned_latest_exit=date(2026, 3, 20),
            underlying_price=150.0,
            avg_daily_volume=5_000_000,
            option_open_interest=2_000,
            option_volume=400,
            bid=2.45,
            ask=2.55,
            option_quote_age_seconds=10,
            underlying_quote_age_seconds=2,
            close=102.0,
            dma20=100.0,
            atr20=2.0,
            adx14=40.0,
            iv_hv_ratio=1.50,
            market_breadth_pct_above_20dma=65.0,
            expected_move_fit=True,
        ),
        CandidateEvaluationInput(
            symbol="SPY",
            market_regime=MarketRegime.TREND_UP,
            directional_state=DirectionalState.NEUTRAL,
            iv_state=IVState.IV_RICH,
            earnings_date=None,
            planned_latest_exit=date(2026, 3, 20),
            underlying_price=150.0,
            avg_daily_volume=5_000_000,
            option_open_interest=2_000,
            option_volume=400,
            bid=2.45,
            ask=2.55,
            option_quote_age_seconds=10,
            underlying_quote_age_seconds=2,
            close=102.0,
            dma20=100.0,
            atr20=2.0,
            expected_move_fit=True,
        ),
    ]

    return [evaluate_candidate_decision(evaluation_input) for evaluation_input in inputs]


def main() -> None:
    decisions = build_sample_decisions()
    result = build_and_write_scan_artifact(decisions=decisions)
    print(f"run_id={result.scan_result.run_id}")
    print(f"output_path={result.output_path}")
    print(
        "summary="
        f"total={result.scan_result.summary.total_candidates},"
        f"passed={result.scan_result.summary.total_passed},"
        f"rejected={result.scan_result.summary.total_rejected}"
    )


if __name__ == "__main__":
    main()
