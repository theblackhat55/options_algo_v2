from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from options_algo_v2.services.historical_row_provider_factory import (
    build_historical_row_provider,
)
from options_algo_v2.services.options_chain_provider_factory import (
    build_options_chain_provider,
    get_options_chain_provider_name,
    get_options_chain_provider_source,
)
from options_algo_v2.services.options_context_service import compute_options_context_snapshot
from options_algo_v2.services.options_context_sqlite_store import (
    upsert_options_context_snapshots,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build options-context snapshot from a base watchlist."
    )
    parser.add_argument(
        "watchlist_path",
        help="Path to base watchlist JSON (for example data/watchlists/watchlist_<run_id>.json)",
    )
    parser.add_argument(
        "--db-path",
        default="data/cache/market_history_watchlist60.db",
        help="SQLite database path for upserting options_context_daily rows.",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="Optional replay end date (YYYY-MM-DD); resolves to previous business day for snapshot dating.",
    )
    return parser.parse_args(argv)


def _load_watchlist_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise RuntimeError("watchlist payload rows must be a list")
    return [row for row in rows if isinstance(row, dict)]


def _resolve_requested_end_date_for_context(end_date: str | None) -> str | None:
    if end_date is None:
        return None

    resolved = date.fromisoformat(end_date)
    while resolved.weekday() >= 5:
        resolved -= timedelta(days=1)
    return resolved.isoformat()


def _build_as_of_utc(end_date: str | None) -> str:
    resolved_end_date = _resolve_requested_end_date_for_context(end_date)
    if resolved_end_date is None:
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return f"{resolved_end_date}T23:59:59Z"


def _extract_spot_price_from_row(row: dict[str, object]) -> float | None:
    for key in ("close", "spot_price", "underlying_price", "price", "last"):
        value = _to_float(row.get(key))
        if value is not None and value > 0:
            return value
    return None


def _latest_close_from_bar_rows(bar_rows: list[dict[str, object]]) -> float | None:
    if not bar_rows:
        return None

    latest_row = None
    latest_ts = None
    for row in bar_rows:
        ts = row.get("ts_event")
        if not isinstance(ts, str) or not ts:
            continue
        if latest_ts is None or ts > latest_ts:
            latest_ts = ts
            latest_row = row

    if not isinstance(latest_row, dict):
        return None

    return _to_float(latest_row.get("close"))


def _resolve_spot_price(
    *,
    base_row: dict[str, object],
    symbol: str,
    row_provider: object,
    resolved_end_date: str | None,
) -> tuple[float | None, str]:
    direct_spot = _extract_spot_price_from_row(base_row)
    if direct_spot is not None and direct_spot > 0:
        return direct_spot, "watchlist"

    get_bar_rows = getattr(row_provider, "get_bar_rows", None)
    if callable(get_bar_rows):
        try:
            bar_rows = get_bar_rows(
                symbol=symbol,
                dataset="XNAS.ITCH",
                schema="ohlcv-1d",
                end_date=resolved_end_date,
            )
        except Exception:
            bar_rows = []

        fallback_spot = _latest_close_from_bar_rows(bar_rows)
        if fallback_spot is not None and fallback_spot > 0:
            return fallback_spot, "historical_rows"

    return None, "missing"


def build_options_context_snapshot(
    watchlist_path: str,
    db_path: str = "data/cache/market_history_watchlist60.db",
    end_date: str | None = None,
) -> str:
    base_path = Path(watchlist_path)
    base_rows = _load_watchlist_rows(base_path)

    provider = build_options_chain_provider()
    provider_name = get_options_chain_provider_name()
    provider_source = get_options_chain_provider_source()
    historical_row_provider = build_historical_row_provider()

    as_of_utc = _build_as_of_utc(end_date)
    resolved_end_date = _resolve_requested_end_date_for_context(end_date)

    snapshots = []
    low_confidence_symbols: list[str] = []
    spot_price_source_counts: dict[str, int] = {}

    for base_row in base_rows:
        symbol = str(base_row["symbol"])
        spot_price, spot_price_source = _resolve_spot_price(
            base_row=base_row,
            symbol=symbol,
            row_provider=historical_row_provider,
            resolved_end_date=resolved_end_date,
        )
        spot_price_source_counts[spot_price_source] = (
            spot_price_source_counts.get(spot_price_source, 0) + 1
        )

        chain = provider.get_chain(symbol)
        snapshot = compute_options_context_snapshot(
            symbol=symbol,
            as_of_utc=as_of_utc,
            spot_price=spot_price,
            chain=chain,
            source_provider=provider_source,
        )
        snapshots.append(snapshot)

        if snapshot.confidence_score < 0.5:
            low_confidence_symbols.append(symbol)

    sqlite_db_path = upsert_options_context_snapshots(
        db_path=db_path,
        snapshots=snapshots,
    )

    print(f"watchlist_path={base_path}")
    print(f"options_chain_provider={provider_name}")
    print(f"options_chain_provider_source={provider_source}")
    print(f"as_of_utc={as_of_utc}")
    print(f"resolved_end_date={resolved_end_date}")
    print(f"row_count={len(snapshots)}")
    print(f"sqlite_db_path={sqlite_db_path}")
    print(f"spot_price_source_counts={spot_price_source_counts}")
    print(f"low_confidence_symbols={low_confidence_symbols}")

    return str(sqlite_db_path)


def _to_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    build_options_context_snapshot(
        str(args.watchlist_path),
        db_path=args.db_path,
        end_date=args.end_date,
    )
