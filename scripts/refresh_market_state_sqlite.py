from __future__ import annotations

import argparse
import json
from pathlib import Path

from options_algo_v2.services.history_store import DEFAULT_HISTORY_DB_PATH, init_history_store
from options_algo_v2.services.options_context_loader import load_options_context_payload
from backfill_iv_and_features import _load_watchlist, _parse_symbols
from backfill_iv_and_features import main as backfill_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh SQLite market state for history/features/options context readiness."
    )
    parser.add_argument("--symbols", type=str, default=None, help="Comma-separated symbols")
    parser.add_argument("--watchlist", type=str, default=None, help="Watchlist JSON path")
    parser.add_argument("--db-path", type=str, default=str(DEFAULT_HISTORY_DB_PATH))
    parser.add_argument("--lookback-days", type=int, default=90)
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--schema", type=str, default=None)
    parser.add_argument("--force-full-refresh", action="store_true")
    parser.add_argument("--skip-iv-proxy", action="store_true")
    parser.add_argument("--backfill-iv-history", action="store_true")
    parser.add_argument("--historical-iv-limit", type=int, default=250)
    parser.add_argument("--check-options-context", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    if not symbols:
        symbols = _load_watchlist(args.watchlist)

    if not symbols:
        raise SystemExit("no symbols provided")

    db_path = Path(args.db_path)
    init_history_store(db_path)

    argv = [
        "backfill_iv_and_features.py",
        "--symbols", ",".join(symbols),
        "--db-path", str(db_path),
        "--lookback-days", str(args.lookback_days),
    ]
    if args.dataset:
        argv += ["--dataset", args.dataset]
    if args.schema:
        argv += ["--schema", args.schema]
    if args.force_full_refresh:
        argv += ["--force-full-refresh"]
    if args.skip_iv_proxy:
        argv += ["--skip-iv-proxy"]
    if args.backfill_iv_history:
        argv += ["--backfill-iv-history"]
    if args.historical_iv_limit:
        argv += ["--historical-iv-limit", str(args.historical_iv_limit)]

    import sys
    old_argv = sys.argv[:]
    try:
        sys.argv = argv
        rc = backfill_main()
    finally:
        sys.argv = old_argv

    summary = {
        "db_path": str(db_path),
        "symbol_count": len(symbols),
        "symbols": symbols,
        "backfill_rc": rc,
    }

    if args.check_options_context:
        payload = load_options_context_payload(db_path=db_path)
        available_symbols = sorted(
            {
                str(row.get("symbol", "")).upper()
                for row in payload.get("rows", [])
                if isinstance(row, dict) and row.get("symbol")
            }
        )
        summary["options_context_row_count"] = payload.get("row_count", 0)
        summary["options_context_latest_as_of_date"] = payload.get("latest_as_of_date")
        summary["options_context_available_symbols"] = available_symbols
        summary["options_context_missing_symbols"] = sorted(set(symbols) - set(available_symbols))

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
