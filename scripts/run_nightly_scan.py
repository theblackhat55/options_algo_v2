from __future__ import annotations

from datetime import date

from options_algo_v2.adapters.databento_underlying import (
    DatabentoUnderlyingAdapter,
)
from options_algo_v2.services.batch_evaluator import evaluate_raw_feature_batch
from options_algo_v2.services.live_raw_feature_pipeline import (
    build_live_raw_feature_input,
)
from options_algo_v2.services.mock_historical_rows import build_mock_historical_rows
from options_algo_v2.services.scan_artifact_orchestrator import (
    build_and_write_scan_artifact,
)
from options_algo_v2.services.underlying_fetcher_factory import (
    build_underlying_fetcher,
)
from options_algo_v2.services.universe_loader import load_universe_symbols


class MockHistoricalWrapper:
    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> list[dict[str, object]]:
        del dataset, schema
        return build_mock_historical_rows(symbol)


def run_nightly_scan() -> str:
    fetcher = build_underlying_fetcher()
    _adapter = DatabentoUnderlyingAdapter(fetcher=fetcher)

    symbols = load_universe_symbols()
    wrapper = MockHistoricalWrapper()

    raw_features = []
    for symbol in symbols[:10]:
        is_bullish = symbol in {"AAPL", "MSFT", "NVDA", "SPY", "QQQ"}

        raw = build_live_raw_feature_input(
            symbol=symbol,
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
            client_wrapper=wrapper,  # type: ignore[arg-type]
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
