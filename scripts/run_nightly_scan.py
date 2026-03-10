from __future__ import annotations

from datetime import date

from options_algo_v2.services.batch_evaluator import evaluate_raw_feature_batch
from options_algo_v2.services.historical_row_provider_factory import (
    build_historical_row_provider,
)
from options_algo_v2.services.live_raw_feature_pipeline import (
    build_live_raw_feature_input,
)
from options_algo_v2.services.runtime_mode import get_runtime_mode
from options_algo_v2.services.scan_artifact_orchestrator import (
    build_and_write_scan_artifact,
)
from options_algo_v2.services.universe_loader import load_universe_symbols


def run_nightly_scan() -> str:
    runtime_mode = get_runtime_mode()
    symbols = load_universe_symbols()
    row_provider = build_historical_row_provider()

    raw_features = []
    for symbol in symbols[:10]:
        is_bullish = symbol in {"AAPL", "MSFT", "NVDA", "SPY", "QQQ"}

        raw = build_live_raw_feature_input(
            symbol=symbol,
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
            client_wrapper=row_provider,  # type: ignore[arg-type]
            adx14=22.0 if is_bullish else 10.0,
            iv_rank=70.0 if is_bullish else 45.0,
            iv_hv_ratio=1.30 if is_bullish else 1.10,
            avg_daily_volume=5_000_000 if is_bullish else 2_000_000,
            option_open_interest=2_000,
            option_volume=400,
            bid=2.45,
            ask=2.55,
            option_quote_age_seconds=10,
            underlying_quote_age_seconds=2,
            market_breadth_pct_above_20dma=60.0 if is_bullish else 50.0,
            earnings_date=None,
            entry_date=date(2026, 3, 10),
            dte_days=35,
        )
        raw_features.append(raw)

    decisions = evaluate_raw_feature_batch(raw_features)
    result = build_and_write_scan_artifact(decisions=decisions)

    print(f"runtime_mode={runtime_mode}")
    print(f"run_id={result.scan_result.run_id}")
    print(f"output_path={result.output_path}")
    print(
        "summary="
        f"total={result.scan_result.summary.total_candidates},"
        f"passed={result.scan_result.summary.total_passed},"
        f"rejected={result.scan_result.summary.total_rejected}"
    )
    print(
        "rejection_reason_counts="
        f"{result.scan_result.summary.rejection_reason_counts}"
    )
    print(
        "signal_state_counts="
        f"{result.scan_result.summary.signal_state_counts}"
    )
    print(
        "strategy_type_counts="
        f"{result.scan_result.summary.strategy_type_counts}"
    )

    return str(result.output_path)


def main() -> None:
    run_nightly_scan()


if __name__ == "__main__":
    main()
