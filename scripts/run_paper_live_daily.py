from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_nightly_scan import run_nightly_scan

from options_algo_v2.services.paper_live_logger import (
    append_paper_live_logs,
    default_paper_live_log_paths,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run paper-live nightly scan and append validation logs."
    )
    parser.add_argument(
        "--watchlist",
        type=str,
        default=None,
        help="Path to watchlist JSON",
    )
    parser.add_argument(
        "--validation-dir",
        type=str,
        default="data/validation",
        help="Directory for paper-live JSONL/CSV outputs",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Optional end date in YYYY-MM-DD format",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    artifact_path = run_nightly_scan(
        watchlist_path=args.watchlist,
        end_date=args.end_date,
    )
    payload = json.loads(Path(artifact_path).read_text())

    paths = default_paper_live_log_paths(args.validation_dir)
    append_paper_live_logs(payload=payload, paths=paths)

    print("paper_live_log_paths:")
    print(f"  run_jsonl={paths.run_jsonl}")
    print(f"  symbol_jsonl={paths.symbol_jsonl}")
    print(f"  run_csv={paths.run_csv}")
    print(f"  logged_run_id={payload.get('run_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
