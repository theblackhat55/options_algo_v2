from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from options_algo_v2.services.options_chain_provider_factory import (
    build_options_chain_provider,
    get_options_chain_provider_name,
    get_options_chain_provider_source,
)
from options_algo_v2.services.options_context_service import compute_options_context_snapshot
from options_algo_v2.services.options_context_store import (
    append_options_context_history,
    write_latest_options_context_snapshot,
)


def _parse_args(argv: list[str]) -> Path:
    if not argv:
        raise SystemExit(
            "usage: PYTHONPATH=src python scripts/build_options_context_snapshot.py "
            "data/watchlists/watchlist_<run_id>.json"
        )
    return Path(argv[0])


def _load_watchlist_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise RuntimeError("watchlist payload rows must be a list")
    return [row for row in rows if isinstance(row, dict)]


def build_options_context_snapshot(watchlist_path: str) -> str:
    base_path = Path(watchlist_path)
    base_rows = _load_watchlist_rows(base_path)

    provider = build_options_chain_provider()
    provider_name = get_options_chain_provider_name()
    provider_source = get_options_chain_provider_source()

    as_of_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")

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

    latest_path = write_latest_options_context_snapshot(snapshots)
    history_path = append_options_context_history(snapshots)

    print(f"watchlist_path={base_path}")
    print(f"options_chain_provider={provider_name}")
    print(f"options_chain_provider_source={provider_source}")
    print(f"row_count={len(snapshots)}")
    print(f"latest_snapshot_path={latest_path}")
    print(f"history_path={history_path}")
    print(f"low_confidence_symbols={low_confidence_symbols}")

    return str(latest_path)


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
    build_options_context_snapshot(str(_parse_args(sys.argv[1:])))
