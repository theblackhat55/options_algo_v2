#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path
from typing import Any

from options_algo_v2.services.paper_live_logger import (
    build_run_summary_row,
    build_symbol_rows,
)
from options_algo_v2.services.scan_analytics_store import (
    upsert_scan_run_summary_rows,
    upsert_scan_symbol_decisions,
)


def _load_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _iter_scan_paths(pattern: str, limit: int | None) -> list[Path]:
    paths = [Path(p) for p in sorted(glob.glob(pattern))]
    if limit is not None and limit > 0:
        paths = paths[-limit:]
    return paths


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill scan analytics SQLite tables from scan artifact JSON files."
    )
    parser.add_argument(
        "--pattern",
        default="data/scan_results/scan_*.json",
        help="Glob pattern for scan artifact JSON files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the most recent N matching files.",
    )
    parser.add_argument(
        "--db-path",
        default=os.getenv(
            "MARKET_HISTORY_DB_PATH",
            "data/cache/market_history_watchlist60.db",
        ),
        help="SQLite DB path for analytics tables.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and summarize files without writing to SQLite.",
    )
    parser.add_argument(
        "--run-ids",
        nargs="*",
        default=None,
        help="Optional explicit run_id filter.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    db_path = Path(args.db_path)

    scan_paths = _iter_scan_paths(args.pattern, args.limit)
    if not scan_paths:
        print(f"no scan files matched pattern={args.pattern}")
        return 1

    processed_files = 0
    skipped_files = 0
    run_rows_total = 0
    symbol_rows_total = 0
    included_run_ids: list[str] = []

    run_id_filter = set(args.run_ids) if args.run_ids else None

    for path in scan_paths:
        payload = _load_payload(path)
        run_id = str(payload.get("run_id", "")).strip()
        if not run_id:
            print(f"skipping file without run_id: {path}")
            skipped_files += 1
            continue

        if run_id_filter is not None and run_id not in run_id_filter:
            continue

        run_row = build_run_summary_row(payload)
        symbol_rows = build_symbol_rows(payload)

        if not args.dry_run:
            run_rows_total += upsert_scan_run_summary_rows(
                rows=[run_row],
                db_path=db_path,
            )
            symbol_rows_total += upsert_scan_symbol_decisions(
                rows=symbol_rows,
                db_path=db_path,
            )
        else:
            run_rows_total += 1
            symbol_rows_total += len(symbol_rows)

        processed_files += 1
        included_run_ids.append(run_id)

        print(
            f"processed {path} "
            f"run_id={run_id} "
            f"symbol_rows={len(symbol_rows)} "
            f"dry_run={args.dry_run}"
        )

    print
    print("=== backfill summary ===")
    print(f"db_path={db_path}")
    print(f"pattern={args.pattern}")
    print(f"processed_files={processed_files}")
    print(f"skipped_files={skipped_files}")
    print(f"run_rows_upserted={run_rows_total}")
    print(f"symbol_rows_upserted={symbol_rows_total}")
    print(f"included_run_ids={included_run_ids}")

    return 0 if processed_files else 1


if __name__ == "__main__":
    raise SystemExit(main())
