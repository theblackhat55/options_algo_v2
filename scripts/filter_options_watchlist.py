from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def _parse_args(argv: list[str]) -> tuple[Path, int | None]:
    if not argv:
        raise SystemExit(
            "usage: PYTHONPATH=src python scripts/filter_options_watchlist.py "
            "data/watchlists/options_watchlist_<run_id>.json [--top-n N]"
        )

    source_path = Path(argv[0])
    top_n: int | None = None

    if len(argv) >= 3 and argv[1] == "--top-n":
        try:
            top_n = int(argv[2])
        except ValueError as exc:
            raise SystemExit("--top-n requires an integer") from exc

        if top_n <= 0:
            raise SystemExit("--top-n must be positive")

    return source_path, top_n


def _load_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text())
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise RuntimeError("watchlist rows must be a list")
    return [row for row in rows if isinstance(row, dict)]


def filter_options_watchlist(source_path: str, top_n: int | None = None) -> str:
    path = Path(source_path)
    rows = _load_rows(path)

    viable_rows = [
        row
        for row in rows
        if bool(row.get("options_viable", False))
    ]

    viable_rows.sort(
        key=lambda row: float(row.get("combined_score", 0.0)),
        reverse=True,
    )

    if top_n is not None:
        viable_rows = viable_rows[:top_n]

    run_id = "options_watchlist_filtered_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path("data/watchlists")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{run_id}.json"

    payload = {
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source_watchlist_path": str(path),
        "top_n": top_n,
        "row_count": len(viable_rows),
        "rows": viable_rows,
    }

    output_path.write_text(json.dumps(payload, indent=2))

    top_symbols = [row.get("symbol") for row in viable_rows[:10]]

    print(f"source_watchlist_path={path}")
    print(f"top_n={top_n}")
    print(f"row_count={len(viable_rows)}")
    print(f"output_path={output_path}")
    print(f"top_filtered_symbols={top_symbols}")

    return str(output_path)


if __name__ == "__main__":
    parsed_path, parsed_top_n = _parse_args(sys.argv[1:])
    filter_options_watchlist(str(parsed_path), top_n=parsed_top_n)
