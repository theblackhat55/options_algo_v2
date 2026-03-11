from __future__ import annotations

import json
import sys
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


def _parse_symbols_from_args(argv: list[str]) -> tuple[list[str] | None, Path | None]:
    if not argv:
        return None, None

    if argv[0] == "--symbols-file":
        if len(argv) < 2:
            raise ValueError("--symbols-file requires a path")
        return None, Path(argv[1])

    return argv, None


def _load_symbols_from_file(path: Path) -> list[str]:
    return [
        line.strip().upper()
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def build_watchlist(symbols: list[str] | None = None) -> str:
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
    )

    run_id = "watchlist_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
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
    arg_symbols, symbols_file = _parse_symbols_from_args(sys.argv[1:])

    if symbols_file is not None:
        symbol_list = _load_symbols_from_file(symbols_file)
        build_watchlist(symbol_list)
    else:
        build_watchlist(arg_symbols)
