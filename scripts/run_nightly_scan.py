from __future__ import annotations

import json
import os
from datetime import date

from options_algo_v2.services.batch_evaluator import evaluate_raw_feature_batch
from options_algo_v2.services.historical_row_provider_factory import (
    MockHistoricalRowProvider,
    build_historical_row_provider,
)
from options_algo_v2.services.live_raw_feature_pipeline import (
    build_live_raw_feature_input,
)
from options_algo_v2.services.market_breadth_provider_factory import (
    build_market_breadth_provider,
)
from options_algo_v2.services.runtime_mode import get_runtime_mode
from options_algo_v2.services.scan_artifact_orchestrator import (
    build_and_write_scan_artifact,
)
from options_algo_v2.services.universe_loader import load_universe_symbols


def _get_breadth_override() -> float | None:
    raw = os.getenv("OPTIONS_ALGO_BREADTH_OVERRIDE_PCT_ABOVE_20DMA")
    if raw is None:
        return None
    stripped = raw.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError as exc:
        raise RuntimeError(
            "OPTIONS_ALGO_BREADTH_OVERRIDE_PCT_ABOVE_20DMA must be numeric"
        ) from exc


def _get_market_breadth_pct(symbol: str, breadth_provider: object) -> float:
    override = _get_breadth_override()
    if override is not None:
        return override

    getter = getattr(breadth_provider, "get_pct_above_20dma", None)
    if getter is None:
        raise RuntimeError("market breadth provider does not expose get_pct_above_20dma")
    return float(getter(symbol=symbol))


def _build_raw_feature_with_fallback(
    *,
    symbol: str,
    row_provider: object,
    breadth_provider: object,
) -> tuple[object, str]:
    is_bullish = symbol in {"AAPL", "MSFT", "NVDA", "SPY", "QQQ"}

    common_kwargs = {
        "symbol": symbol,
        "dataset": "XNAS.ITCH",
        "schema": "ohlcv-1d",
        "adx14": 22.0 if is_bullish else 10.0,
        "iv_rank": 70.0 if is_bullish else 45.0,
        "iv_hv_ratio": 1.30 if is_bullish else 1.10,
        "avg_daily_volume": 5_000_000 if is_bullish else 2_000_000,
        "option_open_interest": 2_000,
        "option_volume": 400,
        "bid": 2.45,
        "ask": 2.55,
        "option_quote_age_seconds": 10,
        "underlying_quote_age_seconds": 2,
        "market_breadth_pct_above_20dma": _get_market_breadth_pct(
            symbol=symbol,
            breadth_provider=breadth_provider,
        ),
        "earnings_date": None,
        "entry_date": date(2026, 3, 10),
        "dte_days": 35,
    }

    try:
        raw = build_live_raw_feature_input(
            provider=row_provider,
            **common_kwargs,
        )
        return raw, "primary"
    except ValueError as exc:
        if "no rows provided to build bar history" not in str(exc):
            raise

    fallback_provider = MockHistoricalRowProvider()
    raw = build_live_raw_feature_input(
        provider=fallback_provider,
        **common_kwargs,
    )
    return raw, "mock_historical_fallback"


def run_nightly_scan(symbols: list[str] | None = None) -> str:
    runtime_mode = get_runtime_mode()
    selected_symbols = symbols if symbols is not None else load_universe_symbols()
    row_provider = build_historical_row_provider()
    breadth_provider = build_market_breadth_provider()

    raw_features = []
    historical_provider_modes: dict[str, str] = {}

    for symbol in selected_symbols[:10]:
        raw, provider_mode = _build_raw_feature_with_fallback(
            symbol=symbol,
            row_provider=row_provider,
            breadth_provider=breadth_provider,
        )
        historical_provider_modes[symbol] = provider_mode
        raw_features.append(raw)

    decisions = evaluate_raw_feature_batch(raw_features)
    artifact_result = build_and_write_scan_artifact(decisions=decisions)
    output_path = artifact_result.output_path
    artifact = output_path.read_text()

    payload = json.loads(artifact)
    summary = payload["summary"]
    runtime_metadata = payload["runtime_metadata"]

    print(f"runtime_mode={runtime_mode}")
    print(f"symbols={selected_symbols[:10]}")
    print(f"run_id={payload['run_id']}")
    print(f"output_path={output_path}")
    print(
        "summary="
        f"total={summary['total_candidates']},"
        f"passed={summary['total_passed']},"
        f"rejected={summary['total_rejected']}"
    )
    print(f"rejection_reason_counts={summary['rejection_reason_counts']}")
    print(f"signal_state_counts={summary['signal_state_counts']}")
    print(f"strategy_type_counts={summary['strategy_type_counts']}")
    print(f"historical_provider_modes={historical_provider_modes}")
    print(
        "top_trade_candidate_symbols="
        f"{runtime_metadata.get('top_trade_candidate_symbols', [])}"
    )
    print(
        "top_trade_summary_rows="
        f"{runtime_metadata.get('top_trade_summary_rows', [])}"
    )

    return str(output_path)


if __name__ == "__main__":
    run_nightly_scan()
