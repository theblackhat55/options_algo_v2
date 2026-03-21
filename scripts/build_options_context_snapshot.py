#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from options_algo_v2.models.options_context import OptionsContextSnapshot
from options_algo_v2.services.options_chain_provider_factory import (
    build_options_chain_provider,
    get_options_chain_provider_name,
)
from options_algo_v2.services.options_context_service import compute_options_context_row_from_snapshot
from options_algo_v2.services.options_context_store import (
    append_options_context_history,
    write_latest_options_context_snapshot,
)
from options_algo_v2.services.runtime_mode import get_runtime_mode


def _latest_options_watchlist_path() -> Path:
    candidates = sorted(
        p for p in Path("data/watchlists").glob("options_watchlist_*.json")
        if "options_watchlist_filtered_" not in p.name
    )
    if not candidates:
        raise FileNotFoundError("No unfiltered options watchlist files found under data/watchlists/")
    return candidates[-1]


def _load_watchlist(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _extract_symbols(payload: dict) -> list[str]:
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise RuntimeError("watchlist payload rows must be a list")

    seen: set[str] = set()
    symbols: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").strip()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
    return symbols


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic options context snapshot from live chain data.")
    parser.add_argument(
        "--watchlist",
        type=str,
        default=None,
        help="Path to unfiltered options watchlist JSON. Defaults to latest options_watchlist_<run_id>.json",
    )
    parser.add_argument(
        "--allow-mock",
        action="store_true",
        help="Allow mock provider output. Intended only for testing.",
    )
    args = parser.parse_args()

    watchlist_path = Path(args.watchlist) if args.watchlist else _latest_options_watchlist_path()
    if "options_watchlist_filtered_" in watchlist_path.name:
        raise SystemExit(
            f"Refusing to use filtered watchlist as options-context source: {watchlist_path}. "
            "Use an unfiltered options_watchlist_<run_id>.json file instead."
        )

    payload = _load_watchlist(watchlist_path)
    symbols = _extract_symbols(payload)

    runtime_mode = get_runtime_mode()
    provider_name = get_options_chain_provider_name()
    if provider_name != "polygon" and not args.allow_mock:
        raise SystemExit(
            f"Refusing to build options context with non-live provider "
            f"(runtime_mode={runtime_mode}, provider={provider_name}). "
            f"Set live runtime/env correctly, or use --allow-mock only for testing."
        )

    provider = build_options_chain_provider()

    generated_at_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = f"options_context_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"

    rows = []
    for symbol in symbols:
        snapshot = provider.get_chain(symbol)
        rows.append(compute_options_context_row_from_snapshot(snapshot))

    snapshot = OptionsContextSnapshot(
        run_id=run_id,
        generated_at_utc=generated_at_utc,
        source_watchlist=str(watchlist_path),
        symbol_count=len(rows),
        rows=rows,
    )

    latest_path = write_latest_options_context_snapshot(snapshot)
    history_path = append_options_context_history(snapshot)

    print(f"runtime_mode={runtime_mode}")
    print(f"provider_name={provider_name}")
    print(f"options_context_run_id={run_id}")
    print(f"source_watchlist={watchlist_path}")
    print(f"symbol_count={snapshot.symbol_count}")
    print(f"latest_options_context={latest_path}")
    print(f"options_context_history={history_path}")

    preview = [row.to_dict() for row in snapshot.rows[:5]]
    print(json.dumps({"preview_rows": preview}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
