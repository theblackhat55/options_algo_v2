from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from options_algo_v2.services.databento_settings import load_databento_settings
from options_algo_v2.services.historical_row_provider_factory import (
    build_historical_row_provider,
    get_historical_row_provider_name,
)
from options_algo_v2.services.market_breadth_provider_factory import (
    build_market_breadth_provider,
    get_market_breadth_provider_name,
)
from options_algo_v2.services.runtime_mode import get_runtime_mode
from options_algo_v2.services.universe_loader import load_universe_symbols
from options_algo_v2.services.watchlist_builder import (
    build_watchlist_rows,
    serialize_watchlist_rows,
)


def build_watchlist(
    symbols: list[str] | None = None,
    output_path_override: str | None = None,
    end_date: str | None = None,
) -> str:
    runtime_mode = get_runtime_mode()
    settings = load_databento_settings()

    historical_row_provider = build_historical_row_provider()
    market_breadth_provider = build_market_breadth_provider()

    historical_row_provider_name = get_historical_row_provider_name()
    market_breadth_provider_name = get_market_breadth_provider_name()

    universe = symbols if symbols is not None else load_universe_symbols()

    watchlist_rows = build_watchlist_rows(
        symbols=universe,
        historical_row_provider=historical_row_provider,
        market_breadth_provider=market_breadth_provider,
        dataset=settings.dataset,
        schema=settings.schema,
        historical_row_provider_name=historical_row_provider_name,
        market_breadth_provider_name=market_breadth_provider_name,
        end_date=end_date,
    )

    run_id = "watchlist_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    if output_path_override:
        output_path = Path(output_path_override)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path("data/watchlists")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{run_id}.json"

    payload = {
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "runtime_mode": runtime_mode,
        "symbol_count": len(universe),
        "historical_row_provider": historical_row_provider_name,
        "market_breadth_provider": market_breadth_provider_name,
        "dataset": settings.dataset,
        "schema": settings.schema,
        "rows": serialize_watchlist_rows(watchlist_rows),
    }

    output_path.write_text(json.dumps(payload, indent=2))

    print(f"runtime_mode={runtime_mode}")
    print(f"symbol_count={len(universe)}")
    print(f"historical_row_provider={historical_row_provider_name}")
    print(f"market_breadth_provider={market_breadth_provider_name}")
    print(f"dataset={settings.dataset}")
    print(f"schema={settings.schema}")
    print(f"run_id={run_id}")
    print(f"output_path={output_path}")

    top_symbols = [row.symbol for row in watchlist_rows[:10]]
    print(f"top_watchlist_symbols={top_symbols}")

    return str(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="*", help="Optional explicit symbol list")
    parser.add_argument("--output", help="Optional output watchlist JSON path")
    parser.add_argument(
        "--end-date",
        help="Optional end date in YYYY-MM-DD format (accepted for wrapper compatibility)",
    )
    args = parser.parse_args()

    build_watchlist(
        symbols=args.symbols if args.symbols else None,
        output_path_override=args.output,
        end_date=args.end_date,
    )
