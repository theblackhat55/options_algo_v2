from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from options_algo_v2.services.options_chain_provider_factory import (
    build_options_chain_provider,
    get_options_chain_provider_name,
    get_options_chain_provider_source,
)
from options_algo_v2.services.options_viability_builder import (
    build_options_watchlist_row,
    sort_options_watchlist_rows,
)
from options_algo_v2.services.runtime_mode import get_runtime_mode


def _load_watchlist_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text())
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise RuntimeError("watchlist payload rows must be a list")
    return [row for row in rows if isinstance(row, dict)]


def build_options_watchlist(watchlist_path: str) -> str:
    runtime_mode = get_runtime_mode()
    provider = build_options_chain_provider()
    provider_name = get_options_chain_provider_name()
    provider_source = get_options_chain_provider_source()

    base_path = Path(watchlist_path)
    base_rows = _load_watchlist_rows(base_path)

    enriched_rows = []
    for base_row in base_rows:
        symbol = str(base_row["symbol"])
        chain = provider.get_chain(symbol)
        quotes = getattr(chain, "quotes", [])
        enriched_rows.append(
            build_options_watchlist_row(
                base_row=base_row,
                quotes=list(quotes),
            )
        )

    sorted_rows = sort_options_watchlist_rows(enriched_rows)

    run_id = "options_watchlist_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path("data/watchlists")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{run_id}.json"

    payload = {
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "runtime_mode": runtime_mode,
        "source_watchlist_path": str(base_path),
        "options_chain_provider": provider_name,
        "options_chain_provider_source": provider_source,
        "row_count": len(sorted_rows),
        "rows": [asdict(row) for row in sorted_rows],
    }

    output_path.write_text(json.dumps(payload, indent=2))

    top_symbols = [row.symbol for row in sorted_rows[:10]]
    viable_symbols = [row.symbol for row in sorted_rows if row.options_viable]

    print(f"runtime_mode={runtime_mode}")
    print(f"source_watchlist_path={base_path}")
    print(f"options_chain_provider={provider_name}")
    print(f"options_chain_provider_source={provider_source}")
    print(f"run_id={run_id}")
    print(f"output_path={output_path}")
    print(f"row_count={len(sorted_rows)}")
    print(f"top_options_watchlist_symbols={top_symbols}")
    print(f"options_viable_symbols={viable_symbols}")

    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(
            "usage: PYTHONPATH=src python scripts/build_options_watchlist.py "
            "data/watchlists/watchlist_<run_id>.json"
        )

    build_options_watchlist(sys.argv[1])
