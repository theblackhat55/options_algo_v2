from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from options_algo_v2.services.batch_evaluator import evaluate_raw_feature_batch
from options_algo_v2.services.historical_row_provider_factory import (
    MockHistoricalRowProvider,
    build_historical_row_provider,
)
from options_algo_v2.services.iv_feature_estimator import (
    compute_iv_hv_ratio_from_snapshot_and_bars,
)
from options_algo_v2.services.live_raw_feature_pipeline import (
    build_live_raw_feature_input,
)
from options_algo_v2.services.market_breadth_provider_factory import (
    build_market_breadth_provider,
)
from options_algo_v2.services.options_chain_provider_factory import (
    build_options_chain_provider,
)
from options_algo_v2.services.runtime_execution_settings import (
    get_runtime_execution_settings,
)
from options_algo_v2.services.runtime_mode import get_runtime_mode
from options_algo_v2.services.scan_artifact_orchestrator import (
    build_and_write_scan_artifact,
)
from options_algo_v2.services.universe_loader import load_universe_symbols


def _load_symbols_from_watchlist(path: Path) -> list[str]:
    payload = json.loads(path.read_text())
    rows = payload.get("rows", [])
    symbols: list[str] = []
    for row in rows:
        if isinstance(row, dict):
            symbol = row.get("symbol")
            if isinstance(symbol, str) and symbol.strip():
                symbols.append(symbol.strip().upper())
    return symbols


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


def _get_market_breadth_pct(symbol: str, breadth_provider: object) -> tuple[float, bool]:
    settings = get_runtime_execution_settings()
    override = _get_breadth_override()

    if override is not None:
        if not settings.allow_breadth_override:
            raise RuntimeError(
                "breadth override is disabled in the current execution mode"
            )
        return override, True

    getter = getattr(breadth_provider, "get_pct_above_20dma", None)
    if getter is None:
        raise RuntimeError("market breadth provider does not expose get_pct_above_20dma")
    return float(getter(symbol=symbol)), False


def _get_latest_close(bar_rows: list[dict[str, object]]) -> float | None:
    if not bar_rows:
        return None

    latest = bar_rows[-1]
    close = latest.get("close")
    if isinstance(close, int | float):
        return float(close)
    return None


def _compute_live_iv_hv_ratio(
    *,
    symbol: str,
    row_provider: object,
    options_chain_provider: object,
    dataset: str,
    schema: str,
) -> float | None:
    get_rows = getattr(row_provider, "get_bar_rows", None)
    get_chain = getattr(options_chain_provider, "get_chain", None)

    if get_rows is None or get_chain is None:
        return None

    bar_rows = get_rows(
        symbol=symbol,
        dataset=dataset,
        schema=schema,
    )
    if not isinstance(bar_rows, list) or not bar_rows:
        return None

    latest_close = _get_latest_close(bar_rows)
    if latest_close is None or latest_close <= 0:
        return None

    snapshot = get_chain(symbol)
    return compute_iv_hv_ratio_from_snapshot_and_bars(
        snapshot=snapshot,
        bar_rows=bar_rows,
        underlying_price=latest_close,
    )


def _build_raw_feature_with_fallback(
    *,
    symbol: str,
    row_provider: object,
    breadth_provider: object,
    options_chain_provider: object,
    as_of_date: date,
) -> tuple[object, str, bool, bool]:
    settings = get_runtime_execution_settings()

    is_bullish = symbol in {"AAPL", "MSFT", "NVDA", "SPY", "QQQ"}
    market_breadth_pct_above_20dma, used_breadth_override = _get_market_breadth_pct(
        symbol=symbol,
        breadth_provider=breadth_provider,
    )

    dataset = "XNAS.ITCH"
    schema = "ohlcv-1d"

    real_iv_hv_ratio = _compute_live_iv_hv_ratio(
        symbol=symbol,
        row_provider=row_provider,
        options_chain_provider=options_chain_provider,
        dataset=dataset,
        schema=schema,
    )
    used_placeholder_iv_hv_ratio = real_iv_hv_ratio is None

    common_kwargs = {
        "symbol": symbol,
        "dataset": dataset,
        "schema": schema,
        "iv_rank": 70.0 if is_bullish else 45.0,
        "iv_hv_ratio": (
            real_iv_hv_ratio
            if real_iv_hv_ratio is not None
            else (1.30 if is_bullish else 1.10)
        ),
        "avg_daily_volume": 5_000_000 if is_bullish else 2_000_000,
        "option_open_interest": 2_000,
        "option_volume": 400,
        "bid": 2.45,
        "ask": 2.55,
        "option_quote_age_seconds": 10,
        "underlying_quote_age_seconds": 2,
        "market_breadth_pct_above_20dma": market_breadth_pct_above_20dma,
        "earnings_date": None,
        "entry_date": as_of_date,
        "dte_days": 35,
    }

    try:
        raw = build_live_raw_feature_input(
            provider=row_provider,
            **common_kwargs,
        )
        return raw, "primary", used_breadth_override, used_placeholder_iv_hv_ratio
    except ValueError as exc:
        if "no rows provided to build bar history" not in str(exc):
            raise

    if not settings.allow_mock_historical_fallback:
        raise RuntimeError(
            f"live historical rows unavailable for symbol={symbol} and mock fallback is disabled"
        )

    fallback_provider = MockHistoricalRowProvider()
    raw = build_live_raw_feature_input(
        provider=fallback_provider,
        **common_kwargs,
    )
    return raw, "mock_historical_fallback", used_breadth_override, used_placeholder_iv_hv_ratio


def run_nightly_scan(
    symbols: list[str] | None = None,
    watchlist_path: str | None = None,
) -> str:
    runtime_mode = get_runtime_mode()
    execution_settings = get_runtime_execution_settings()

    if watchlist_path is not None:
        selected_symbols = _load_symbols_from_watchlist(Path(watchlist_path))
    elif symbols is None:
        selected_symbols = load_universe_symbols()[:10]
    else:
        selected_symbols = symbols

    row_provider = build_historical_row_provider()
    breadth_provider = build_market_breadth_provider()
    options_chain_provider = build_options_chain_provider()

    raw_features = []
    historical_provider_modes: dict[str, str] = {}
    breadth_override_symbols: list[str] = []
    placeholder_iv_rank_symbols: list[str] = []
    placeholder_iv_hv_ratio_symbols: list[str] = []

    for symbol in selected_symbols:
        raw, provider_mode, used_breadth_override, used_placeholder_iv_hv_ratio = (
            _build_raw_feature_with_fallback(
                symbol=symbol,
                row_provider=row_provider,
                breadth_provider=breadth_provider,
                options_chain_provider=options_chain_provider,
                as_of_date=execution_settings.as_of_date,
            )
        )
        historical_provider_modes[symbol] = provider_mode
        placeholder_iv_rank_symbols.append(symbol)
        if used_placeholder_iv_hv_ratio:
            placeholder_iv_hv_ratio_symbols.append(symbol)
        if used_breadth_override:
            breadth_override_symbols.append(symbol)
        raw_features.append(raw)

    used_mock_historical_fallback = any(
        mode == "mock_historical_fallback"
        for mode in historical_provider_modes.values()
    )
    used_placeholder_iv_rank_inputs = bool(placeholder_iv_rank_symbols)
    used_placeholder_iv_hv_ratio_inputs = bool(placeholder_iv_hv_ratio_symbols)
    used_placeholder_iv_inputs = (
        used_placeholder_iv_rank_inputs or used_placeholder_iv_hv_ratio_inputs
    )
    degraded_live_mode = (
        bool(breadth_override_symbols)
        or used_mock_historical_fallback
        or used_placeholder_iv_inputs
    )

    if execution_settings.strict_live_mode and (
        used_placeholder_iv_rank_inputs or used_placeholder_iv_hv_ratio_inputs
    ):
        raise RuntimeError(
            "placeholder IV inputs are not allowed in strict live mode"
        )

    decisions = evaluate_raw_feature_batch(raw_features)
    artifact_result = build_and_write_scan_artifact(
        decisions=decisions,
        degraded_metadata={
            "as_of_date": execution_settings.as_of_date.isoformat(),
            "strict_live_mode": execution_settings.strict_live_mode,
            "used_mock_historical_fallback": used_mock_historical_fallback,
            "historical_provider_modes": historical_provider_modes,
            "used_breadth_override": bool(breadth_override_symbols),
            "breadth_override_symbols": breadth_override_symbols,
            "used_placeholder_iv_inputs": used_placeholder_iv_inputs,
            "used_placeholder_iv_rank_inputs": used_placeholder_iv_rank_inputs,
            "used_placeholder_iv_hv_ratio_inputs": used_placeholder_iv_hv_ratio_inputs,
            "placeholder_iv_rank_symbols": placeholder_iv_rank_symbols,
            "placeholder_iv_hv_ratio_symbols": placeholder_iv_hv_ratio_symbols,
            "degraded_live_mode": degraded_live_mode,
        },
    )
    output_path = artifact_result.output_path
    artifact = output_path.read_text()

    payload = json.loads(artifact)
    summary = payload["summary"]
    runtime_metadata = payload["runtime_metadata"]

    print(f"runtime_mode={runtime_mode}")
    print(f"symbols={selected_symbols}")
    print(f"as_of_date={execution_settings.as_of_date.isoformat()}")
    print(f"strict_live_mode={execution_settings.strict_live_mode}")
    print(f"run_id={payload['run_id']}")
    print(f"output_path={output_path}")

    if degraded_live_mode:
        print("WARNING: degraded_live_mode=true")
    if used_mock_historical_fallback:
        print("WARNING: mock historical fallback was used")
    if breadth_override_symbols:
        print(f"WARNING: breadth override used for symbols={breadth_override_symbols}")
    if placeholder_iv_rank_symbols:
        print(
            "WARNING: placeholder IV rank inputs used for symbols="
            f"{placeholder_iv_rank_symbols}"
        )
    if placeholder_iv_hv_ratio_symbols:
        print(
            "WARNING: placeholder IV/HV ratio inputs used for symbols="
            f"{placeholder_iv_hv_ratio_symbols}"
        )

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
    print(f"breadth_override_symbols={breadth_override_symbols}")
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
