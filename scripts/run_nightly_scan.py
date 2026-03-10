from __future__ import annotations

from options_algo_v2.adapters.databento_underlying import (
    DatabentoUnderlyingAdapter,
)
from options_algo_v2.services.batch_evaluator import evaluate_raw_feature_batch
from options_algo_v2.services.runtime_mode import get_runtime_mode
from options_algo_v2.services.sample_feature_factory import (
    build_sample_raw_features_from_snapshot,
)
from options_algo_v2.services.scan_artifact_orchestrator import (
    build_and_write_scan_artifact,
)
from options_algo_v2.services.universe_loader import load_universe_symbols


def fake_underlying_fetcher(symbol: str) -> dict[str, object]:
    bullish_prices = {
        "AAPL": 210.0,
        "MSFT": 420.0,
        "NVDA": 140.0,
        "META": 500.0,
        "SPY": 520.0,
        "QQQ": 450.0,
    }

    close = bullish_prices.get(symbol.upper(), 100.0)
    volume = 5_000_000 if symbol.upper() in bullish_prices else 2_000_000

    return {
        "close": close,
        "volume": volume,
        "timestamp": "2026-03-10T21:00:00Z",
    }


def run_nightly_scan() -> str:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        raise NotImplementedError("live runtime mode is not wired yet")

    symbols = load_universe_symbols()
    adapter = DatabentoUnderlyingAdapter(fetcher=fake_underlying_fetcher)

    raw_features = []
    for symbol in symbols[:10]:
        snapshot = adapter.get_snapshot(symbol)
        raw = build_sample_raw_features_from_snapshot(snapshot)
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
