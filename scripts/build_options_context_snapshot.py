from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

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

    as_of_utc = _build_as_of_utc(end_date)

    snapshots = []
    low_confidence_symbols: list[str] = []

    for base_row in base_rows:
        symbol = str(base_row["symbol"])
        spot_price = _to_float(base_row.get("close"))

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
    print(f"resolved_end_date={_resolve_requested_end_date_for_context(end_date)}")
    print(f"row_count={len(snapshots)}")
    print(f"sqlite_db_path={sqlite_db_path}")
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
