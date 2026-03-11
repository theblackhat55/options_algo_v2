from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.batch_evaluator import evaluate_raw_feature_batch
from options_algo_v2.services.historical_row_provider_factory import (
    MockHistoricalRowProvider,
    build_historical_row_provider,
)
from options_algo_v2.services.iv_feature_estimator import (
    compute_iv_hv_ratio_from_snapshot_and_bars,
    estimate_near_atm_implied_vol,
)
from options_algo_v2.services.iv_rank_history import (
    IvProxyObservation,
    append_iv_proxy_observation,
    compute_iv_rank_from_history,
    count_iv_proxy_observations,
    default_iv_rank_history_path,
    list_iv_proxy_observation_counts,
)
from options_algo_v2.services.live_raw_feature_pipeline import (
    build_live_raw_feature_input,
    build_live_raw_feature_input_from_rows,
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

IV_RANK_TRAILING_OBSERVATIONS = 20


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


def _get_bar_rows(
    *,
    row_provider: object,
    symbol: str,
    dataset: str,
    schema: str,
) -> list[dict[str, object]]:
    get_rows = getattr(row_provider, "get_bar_rows", None)
    if get_rows is None:
        return []
    rows = get_rows(
        symbol=symbol,
        dataset=dataset,
        schema=schema,
    )
    if not isinstance(rows, list):
        return []
    return rows


def _get_options_snapshot(
    *,
    options_chain_provider: object,
    symbol: str,
) -> OptionsChainSnapshot | None:
    get_chain = getattr(options_chain_provider, "get_chain", None)
    if get_chain is None:
        return None
    snapshot = get_chain(symbol)
    if not isinstance(snapshot, OptionsChainSnapshot):
        return None
    return snapshot


def _build_quote_quality_counts(
    snapshot: OptionsChainSnapshot | None,
) -> dict[str, int]:
    quotes = list(snapshot.quotes) if snapshot is not None else []

    counts = {
        "total_quotes": 0,
        "real_quotes": 0,
        "synthetic_quotes": 0,
        "missing_iv_quotes": 0,
        "missing_delta_quotes": 0,
        "zero_open_interest_quotes": 0,
        "zero_volume_quotes": 0,
        "wide_spread_quotes": 0,
    }

    for quote in quotes:
        bid = float(quote.bid or 0.0)
        ask = float(quote.ask or 0.0)
        mid = float(quote.mid or 0.0)
        implied_volatility = quote.implied_volatility
        delta = quote.delta
        open_interest = int(quote.open_interest or 0)
        volume = int(quote.volume or 0)

        counts["total_quotes"] += 1

        has_real_two_sided_quote = bid > 0.0 and ask > 0.0 and ask >= bid
        if has_real_two_sided_quote:
            counts["real_quotes"] += 1
            spread_pct = ((ask - bid) / mid) if mid > 0.0 else 0.0
            if spread_pct > 0.10:
                counts["wide_spread_quotes"] += 1
        else:
            counts["synthetic_quotes"] += 1

        if implied_volatility is None:
            counts["missing_iv_quotes"] += 1
        if delta is None:
            counts["missing_delta_quotes"] += 1
        if open_interest <= 0:
            counts["zero_open_interest_quotes"] += 1
        if volume <= 0:
            counts["zero_volume_quotes"] += 1

    return counts


def _merge_quote_quality_counts(
    aggregate: dict[str, int],
    symbol_counts: dict[str, int],
) -> dict[str, int]:
    merged = dict(aggregate)
    for key, value in symbol_counts.items():
        merged[key] = int(merged.get(key, 0)) + int(value)
    return merged


def _get_latest_close(bar_rows: list[dict[str, object]]) -> float | None:
    if not bar_rows:
        return None

    latest = bar_rows[-1]
    close = latest.get("close")
    if isinstance(close, int | float):
        return float(close)
    return None


def _average_daily_volume_from_bar_rows(bar_rows: list[dict[str, object]]) -> float | None:
    volumes = [
        float(row["volume"])
        for row in bar_rows
        if isinstance(row, dict) and isinstance(row.get("volume"), int | float)
    ]
    if not volumes:
        return None
    return sum(volumes) / len(volumes)


def _quote_quality_key(
    quote: OptionQuote,
    *,
    underlying_price: float,
) -> tuple[float, float, int, int]:
    distance = abs(quote.strike - underlying_price)
    spread_width = max(0.0, quote.ask - quote.bid)
    return (
        distance,
        spread_width,
        -int(quote.open_interest),
        -int(quote.volume),
    )


def _select_reference_quote(
    *,
    snapshot: OptionsChainSnapshot,
    underlying_price: float,
) -> OptionQuote | None:
    candidates = [
        quote
        for quote in snapshot.quotes
        if quote.bid > 0
        and quote.ask > 0
        and quote.ask >= quote.bid
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda quote: _quote_quality_key(
            quote,
            underlying_price=underlying_price,
        )
    )
    return candidates[0]


def _serialize_reference_quote(quote: OptionQuote | None) -> dict[str, object] | None:
    if quote is None:
        return None
    return {
        "option_symbol": quote.option_symbol,
        "expiration": quote.expiration,
        "strike": float(quote.strike),
        "option_type": quote.option_type,
        "bid": float(quote.bid),
        "ask": float(quote.ask),
        "mid": float(quote.mid),
        "delta": None if quote.delta is None else float(quote.delta),
        "implied_volatility": (
            None
            if quote.implied_volatility is None
            else float(quote.implied_volatility)
        ),
        "open_interest": int(quote.open_interest),
        "volume": int(quote.volume),
    }


def _compute_live_iv_metrics(
    *,
    symbol: str,
    bar_rows: list[dict[str, object]],
    snapshot: OptionsChainSnapshot | None,
    as_of_date: date,
) -> tuple[float | None, float | None]:
    latest_close = _get_latest_close(bar_rows)
    if latest_close is None or latest_close <= 0 or snapshot is None:
        return None, None

    implied_vol_proxy = estimate_near_atm_implied_vol(
        snapshot=snapshot,
        underlying_price=latest_close,
    )

    iv_hv_ratio = compute_iv_hv_ratio_from_snapshot_and_bars(
        snapshot=snapshot,
        bar_rows=bar_rows,
        underlying_price=latest_close,
    )

    if implied_vol_proxy is not None:
        history_path = default_iv_rank_history_path()
        append_iv_proxy_observation(
            path=history_path,
            observation=IvProxyObservation(
                as_of_date=as_of_date.isoformat(),
                symbol=symbol,
                implied_vol_proxy=implied_vol_proxy,
            ),
        )
        iv_rank = compute_iv_rank_from_history(
            path=history_path,
            symbol=symbol,
            trailing_observations=IV_RANK_TRAILING_OBSERVATIONS,
        )
    else:
        iv_rank = None

    return iv_rank, iv_hv_ratio


def _build_live_liquidity_inputs(
    *,
    symbol: str,
    bar_rows: list[dict[str, object]],
    snapshot: OptionsChainSnapshot | None,
) -> tuple[dict[str, int | float], bool]:
    latest_close = _get_latest_close(bar_rows)
    avg_daily_volume = _average_daily_volume_from_bar_rows(bar_rows)

    if latest_close is None or snapshot is None or avg_daily_volume is None:
        return {
            "avg_daily_volume": 2_000_000.0,
            "option_open_interest": 2_000,
            "option_volume": 400,
            "bid": 2.45,
            "ask": 2.55,
            "option_quote_age_seconds": 10,
            "underlying_quote_age_seconds": 2,
        }, True

    reference_quote = _select_reference_quote(
        snapshot=snapshot,
        underlying_price=latest_close,
    )
    if reference_quote is None:
        return {
            "avg_daily_volume": avg_daily_volume,
            "option_open_interest": 2_000,
            "option_volume": 400,
            "bid": 2.45,
            "ask": 2.55,
            "option_quote_age_seconds": 10,
            "underlying_quote_age_seconds": 2,
        }, True

    return {
        "avg_daily_volume": avg_daily_volume,
        "option_open_interest": int(reference_quote.open_interest),
        "option_volume": int(reference_quote.volume),
        "bid": float(reference_quote.bid),
        "ask": float(reference_quote.ask),
        "option_quote_age_seconds": 10,
        "underlying_quote_age_seconds": 2,
    }, False


def _build_liquidity_debug_info(
    *,
    symbol: str,
    bar_rows: list[dict[str, object]],
    snapshot: OptionsChainSnapshot | None,
) -> dict[str, object]:
    latest_close = _get_latest_close(bar_rows)
    avg_daily_volume = _average_daily_volume_from_bar_rows(bar_rows)
    reference_quote = None
    if latest_close is not None and latest_close > 0 and snapshot is not None:
        reference_quote = _select_reference_quote(
            snapshot=snapshot,
            underlying_price=latest_close,
        )

    liquidity_inputs, used_placeholder_liquidity_inputs = _build_live_liquidity_inputs(
        symbol=symbol,
        bar_rows=bar_rows,
        snapshot=snapshot,
    )

    return {
        "symbol": symbol,
        "latest_close": latest_close,
        "avg_daily_volume_from_bars": avg_daily_volume,
        "snapshot_source": None if snapshot is None else snapshot.source,
        "snapshot_as_of": None if snapshot is None else snapshot.as_of,
        "quote_count": 0 if snapshot is None else len(snapshot.quotes),
        "used_placeholder_liquidity_inputs": used_placeholder_liquidity_inputs,
        "selected_reference_quote": _serialize_reference_quote(reference_quote),
        "selected_liquidity_inputs": {
            "avg_daily_volume": float(liquidity_inputs["avg_daily_volume"]),
            "option_open_interest": int(liquidity_inputs["option_open_interest"]),
            "option_volume": int(liquidity_inputs["option_volume"]),
            "bid": float(liquidity_inputs["bid"]),
            "ask": float(liquidity_inputs["ask"]),
            "option_quote_age_seconds": int(liquidity_inputs["option_quote_age_seconds"]),
            "underlying_quote_age_seconds": int(
                liquidity_inputs["underlying_quote_age_seconds"]
            ),
        },
    }


def _build_raw_feature_with_fallback(
    *,
    symbol: str,
    row_provider: object,
    breadth_provider: object,
    options_chain_provider: object,
    as_of_date: date,
) -> tuple[object, str, bool, bool, bool, bool]:
    settings = get_runtime_execution_settings()
    runtime_mode = os.environ.get("OPTIONS_ALGO_RUNTIME_MODE", "mock").strip().lower()

    is_bullish = symbol in {"AAPL", "MSFT", "NVDA", "SPY", "QQQ"}
    market_breadth_pct_above_20dma, used_breadth_override = _get_market_breadth_pct(
        symbol=symbol,
        breadth_provider=breadth_provider,
    )

    dataset = "XNAS.ITCH"
    schema = "ohlcv-1d"

    if runtime_mode != "live":
        try:
            raw = build_live_raw_feature_input(
                symbol=symbol,
                dataset=dataset,
                schema=schema,
                provider=row_provider,
                iv_rank=70.0 if is_bullish else 45.0,
                iv_hv_ratio=1.30 if is_bullish else 1.10,
                avg_daily_volume=8_000_000.0 if is_bullish else 5_000_000.0,
                option_open_interest=2500 if is_bullish else 1800,
                option_volume=800 if is_bullish else 500,
                bid=2.48 if is_bullish else 1.94,
                ask=2.52 if is_bullish else 1.98,
                option_quote_age_seconds=15,
                underlying_quote_age_seconds=2,
                market_breadth_pct_above_20dma=market_breadth_pct_above_20dma,
                earnings_date=None,
                entry_date=as_of_date,
                dte_days=35,
            )
            return raw, "primary", used_breadth_override, True, False, False
        except Exception:
            if not settings.allow_mock_historical_fallback:
                raise
            fallback_provider = MockHistoricalRowProvider()
            raw = build_live_raw_feature_input(
                symbol=symbol,
                dataset=dataset,
                schema=schema,
                provider=fallback_provider,
                iv_rank=70.0 if is_bullish else 45.0,
                iv_hv_ratio=1.30 if is_bullish else 1.10,
                avg_daily_volume=8_000_000.0 if is_bullish else 5_000_000.0,
                option_open_interest=2500 if is_bullish else 1800,
                option_volume=800 if is_bullish else 500,
                bid=2.48 if is_bullish else 1.94,
                ask=2.52 if is_bullish else 1.98,
                option_quote_age_seconds=15,
                underlying_quote_age_seconds=2,
                market_breadth_pct_above_20dma=market_breadth_pct_above_20dma,
                earnings_date=None,
                entry_date=as_of_date,
                dte_days=35,
            )
            return raw, "mock_fallback", used_breadth_override, True, False, False

    bar_rows = _get_bar_rows(
        row_provider=row_provider,
        symbol=symbol,
        dataset=dataset,
        schema=schema,
    )

    snapshot = _get_options_snapshot(
        options_chain_provider=options_chain_provider,
        symbol=symbol,
    )

    real_iv_rank, real_iv_hv_ratio = _compute_live_iv_metrics(
        symbol=symbol,
        bar_rows=bar_rows,
        snapshot=snapshot,
        as_of_date=as_of_date,
    )

    liquidity_inputs, used_placeholder_liquidity_inputs = _build_live_liquidity_inputs(
        symbol=symbol,
        bar_rows=bar_rows,
        snapshot=snapshot,
    )

    used_placeholder_iv_rank = real_iv_rank is None
    used_placeholder_iv_hv_ratio = real_iv_hv_ratio is None

    common_kwargs = {
        "symbol": symbol,
        "iv_rank": (
            real_iv_rank
            if real_iv_rank is not None
            else (70.0 if is_bullish else 45.0)
        ),
        "iv_hv_ratio": (
            real_iv_hv_ratio
            if real_iv_hv_ratio is not None
            else (1.30 if is_bullish else 1.10)
        ),
        "avg_daily_volume": float(liquidity_inputs["avg_daily_volume"]),
        "option_open_interest": int(liquidity_inputs["option_open_interest"]),
        "option_volume": int(liquidity_inputs["option_volume"]),
        "bid": float(liquidity_inputs["bid"]),
        "ask": float(liquidity_inputs["ask"]),
        "option_quote_age_seconds": int(liquidity_inputs["option_quote_age_seconds"]),
        "underlying_quote_age_seconds": int(
            liquidity_inputs["underlying_quote_age_seconds"]
        ),
        "market_breadth_pct_above_20dma": market_breadth_pct_above_20dma,
        "earnings_date": None,
        "entry_date": as_of_date,
        "dte_days": 35,
    }

    try:
        raw = build_live_raw_feature_input_from_rows(
            rows=bar_rows,
            **common_kwargs,
        )
        return (
            raw,
            "primary",
            used_breadth_override,
            used_placeholder_iv_rank,
            used_placeholder_iv_hv_ratio,
            used_placeholder_liquidity_inputs,
        )
    except ValueError as exc:
        if "no rows provided to build bar history" not in str(exc):
            raise

    if not settings.allow_mock_historical_fallback:
        raise RuntimeError(
            f"live historical rows unavailable for symbol={symbol} and mock fallback is disabled"
        )

    fallback_provider = MockHistoricalRowProvider()
    raw = build_live_raw_feature_input(
        symbol=symbol,
        dataset=dataset,
        schema=schema,
        provider=fallback_provider,
        **common_kwargs,
    )
    return (
        raw,
        "mock_historical_fallback",
        used_breadth_override,
        used_placeholder_iv_rank,
        used_placeholder_iv_hv_ratio,
        used_placeholder_liquidity_inputs,
    )


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
    placeholder_liquidity_symbols: list[str] = []
    iv_rank_ready_symbols: list[str] = []
    quote_quality_by_symbol: dict[str, dict[str, int]] = {}
    liquidity_debug_by_symbol: dict[str, dict[str, object]] = {}
    aggregate_quote_quality_counts: dict[str, int] = {
        "total_quotes": 0,
        "real_quotes": 0,
        "synthetic_quotes": 0,
        "missing_iv_quotes": 0,
        "missing_delta_quotes": 0,
        "zero_open_interest_quotes": 0,
        "zero_volume_quotes": 0,
        "wide_spread_quotes": 0,
    }

    for symbol in selected_symbols:
        (
            raw,
            provider_mode,
            used_breadth_override,
            used_placeholder_iv_rank,
            used_placeholder_iv_hv_ratio,
            used_placeholder_liquidity_inputs,
        ) = _build_raw_feature_with_fallback(
            symbol=symbol,
            row_provider=row_provider,
            breadth_provider=breadth_provider,
            options_chain_provider=options_chain_provider,
            as_of_date=execution_settings.as_of_date,
        )
        historical_provider_modes[symbol] = provider_mode

        snapshot_for_quality = _get_options_snapshot(
            options_chain_provider=options_chain_provider,
            symbol=symbol,
        )
        symbol_quote_quality_counts = _build_quote_quality_counts(snapshot_for_quality)
        quote_quality_by_symbol[symbol] = symbol_quote_quality_counts
        aggregate_quote_quality_counts = _merge_quote_quality_counts(
            aggregate_quote_quality_counts,
            symbol_quote_quality_counts,
        )
        bar_rows_for_debug = _get_bar_rows(
            row_provider=row_provider,
            symbol=symbol,
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )
        liquidity_debug_by_symbol[symbol] = _build_liquidity_debug_info(
            symbol=symbol,
            bar_rows=bar_rows_for_debug,
            snapshot=snapshot_for_quality,
        )

        if used_placeholder_iv_rank:
            placeholder_iv_rank_symbols.append(symbol)
        else:
            iv_rank_ready_symbols.append(symbol)
        if used_placeholder_iv_hv_ratio:
            placeholder_iv_hv_ratio_symbols.append(symbol)
        if used_placeholder_liquidity_inputs:
            placeholder_liquidity_symbols.append(symbol)
        if used_breadth_override:
            breadth_override_symbols.append(symbol)
        raw_features.append(raw)

    used_mock_historical_fallback = any(
        mode == "mock_historical_fallback"
        for mode in historical_provider_modes.values()
    )
    used_placeholder_iv_rank_inputs = bool(placeholder_iv_rank_symbols)
    used_placeholder_iv_hv_ratio_inputs = bool(placeholder_iv_hv_ratio_symbols)
    used_placeholder_liquidity_inputs = bool(placeholder_liquidity_symbols)
    used_placeholder_iv_inputs = (
        used_placeholder_iv_rank_inputs or used_placeholder_iv_hv_ratio_inputs
    )
    degraded_live_mode = (
        bool(breadth_override_symbols)
        or used_mock_historical_fallback
        or used_placeholder_iv_inputs
        or used_placeholder_liquidity_inputs
    )

    if execution_settings.strict_live_mode and (
        used_placeholder_iv_rank_inputs
        or used_placeholder_iv_hv_ratio_inputs
        or used_placeholder_liquidity_inputs
    ):
        raise RuntimeError(
            "placeholder live inputs are not allowed in strict live mode"
        )

    history_path = default_iv_rank_history_path()

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
            "used_placeholder_liquidity_inputs": used_placeholder_liquidity_inputs,
            "placeholder_iv_rank_symbols": placeholder_iv_rank_symbols,
            "placeholder_iv_hv_ratio_symbols": placeholder_iv_hv_ratio_symbols,
            "placeholder_liquidity_symbols": placeholder_liquidity_symbols,
            "iv_rank_ready_symbols": iv_rank_ready_symbols,
            "iv_rank_insufficient_history_symbols": placeholder_iv_rank_symbols,
            "iv_rank_history_path": str(history_path),
            "iv_rank_trailing_observations": IV_RANK_TRAILING_OBSERVATIONS,
            "iv_rank_observation_counts": list_iv_proxy_observation_counts(history_path),
            "iv_rank_observation_count_by_symbol": {
                symbol: count_iv_proxy_observations(path=history_path, symbol=symbol)
                for symbol in selected_symbols
            },
            "quote_quality_by_symbol": quote_quality_by_symbol,
            "aggregate_quote_quality_counts": aggregate_quote_quality_counts,
            "liquidity_debug_by_symbol": liquidity_debug_by_symbol,
            "degraded_live_mode": degraded_live_mode,
        },
    )
    output_path = artifact_result.output_path
    artifact = output_path.read_text()

    payload = json.loads(artifact)
    summary = payload["summary"]
    runtime_metadata = payload["runtime_metadata"]

    resolved_runtime_mode = str(runtime_metadata.get("runtime_mode", runtime_mode))

    print(f"runtime_mode={resolved_runtime_mode}")
    print(f"symbols={selected_symbols}")
    print(f"as_of_date={execution_settings.as_of_date.isoformat()}")
    print(f"strict_live_mode={execution_settings.strict_live_mode}")
    print(f"run_id={payload['run_id']}")
    print(f"output_path={output_path}")

    if resolved_runtime_mode == "live":
        if degraded_live_mode:
            print("WARNING: degraded_live_mode=true")
        if used_mock_historical_fallback:
            print("WARNING: mock historical fallback was used")
        if breadth_override_symbols:
            print(
                f"WARNING: breadth override used for symbols={breadth_override_symbols}"
            )
        if placeholder_iv_rank_symbols:
            print(
                "WARNING: placeholder IV rank inputs used for symbols="
                f"{placeholder_iv_rank_symbols}"
            )
        print(f"iv_rank_ready_symbols={iv_rank_ready_symbols}")
        print(f"iv_rank_insufficient_history_symbols={placeholder_iv_rank_symbols}")
        print(f"iv_rank_history_path={history_path}")
        print(f"iv_rank_trailing_observations={IV_RANK_TRAILING_OBSERVATIONS}")
        print(
            "iv_rank_observation_count_by_symbol="
            f"{runtime_metadata.get('iv_rank_observation_count_by_symbol', {})}"
        )
        if placeholder_iv_hv_ratio_symbols:
            print(
                "WARNING: placeholder IV/HV ratio inputs used for symbols="
                f"{placeholder_iv_hv_ratio_symbols}"
            )
        if placeholder_liquidity_symbols:
            print(
                "WARNING: placeholder liquidity inputs used for symbols="
                f"{placeholder_liquidity_symbols}"
            )
        print(
            "aggregate_quote_quality_counts="
            f"{runtime_metadata.get('aggregate_quote_quality_counts', {})}"
        )
        liquidity_debug_by_symbol = runtime_metadata.get("liquidity_debug_by_symbol", {})
        if liquidity_debug_by_symbol:
            first_symbol = sorted(liquidity_debug_by_symbol.keys())[0]
            print(
                "sample_liquidity_debug="
                f"{first_symbol}:{liquidity_debug_by_symbol[first_symbol]}"
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
    spread_debug_by_symbol = runtime_metadata.get(
        "trade_candidate_spread_debug_by_symbol",
        {},
    )
    if spread_debug_by_symbol:
        first_symbol = sorted(spread_debug_by_symbol.keys())[0]
        print(
            "sample_trade_candidate_spread_debug="
            f"{first_symbol}:{spread_debug_by_symbol[first_symbol][:2]}"
        )

    return str(output_path)


if __name__ == "__main__":
    run_nightly_scan()
