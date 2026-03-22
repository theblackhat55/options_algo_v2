from __future__ import annotations

import argparse
import json
from pathlib import Path

from options_algo_v2.adapters.databento_live_historical_row_client import (
    DatabentoLiveHistoricalRowClient,
)
from options_algo_v2.adapters.polygon_historical_options_chain_client import (
    PolygonHistoricalOptionsChainClient,
)
from options_algo_v2.services.databento_historical_fetcher import (
    fetch_databento_daily_rows,
)
from options_algo_v2.services.databento_settings import load_databento_settings
from options_algo_v2.services.history_backfill import backfill_symbol_history
from options_algo_v2.services.history_store import DEFAULT_HISTORY_DB_PATH, init_history_store
from options_algo_v2.services.historical_iv_proxy_backfill import (
    backfill_historical_iv_proxy_for_symbol,
)
from options_algo_v2.services.options_chain_provider_factory import build_options_chain_provider
from options_algo_v2.services.polygon_settings import PolygonSettings


def _parse_symbols(symbols_arg: str | None) -> list[str]:
    if not symbols_arg:
        return []
    return [part.strip().upper() for part in symbols_arg.split(",") if part.strip()]


def _load_watchlist(path: str | None) -> list[str]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, dict):
        if isinstance(payload.get("symbols"), list):
            return [str(item).upper() for item in payload["symbols"]]
    if isinstance(payload, list):
        return [str(item).upper() for item in payload]
    raise ValueError(f"unsupported watchlist format: {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill reusable history cache")
    parser.add_argument("--symbols", type=str, default=None, help="Comma-separated symbols")
    parser.add_argument("--watchlist", type=str, default=None, help="Watchlist JSON path")
    parser.add_argument("--lookback-days", type=int, default=90, help="Historical bars lookback")
    parser.add_argument("--dataset", type=str, default=None, help="Historical dataset override")
    parser.add_argument("--schema", type=str, default=None, help="Historical schema override")
    parser.add_argument("--db-path", type=str, default=str(DEFAULT_HISTORY_DB_PATH))
    parser.add_argument("--force-full-refresh", action="store_true")
    parser.add_argument("--skip-iv-proxy", action="store_true", help="Do not fetch latest IV proxy")
    parser.add_argument(
        "--backfill-iv-history",
        action="store_true",
        help="Fetch historical IV proxy rows by date from Polygon/Massive",
    )
    parser.add_argument(
        "--historical-iv-limit",
        type=int,
        default=250,
        help="Per-day Polygon snapshot limit for historical options chain fetch",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    if not symbols:
        symbols = _load_watchlist(args.watchlist)

    if not symbols:
        raise SystemExit("no symbols provided")

    settings = load_databento_settings()
    dataset = args.dataset or settings.dataset
    schema = args.schema or settings.schema

    db_path = Path(args.db_path)
    init_history_store(db_path)

    historical_client = DatabentoLiveHistoricalRowClient(
        settings=settings,
        fetch_rows=fetch_databento_daily_rows,
    )

    options_chain_provider = None
    if not args.skip_iv_proxy:
        options_chain_provider = build_options_chain_provider()

    historical_polygon_client = None
    if args.backfill_iv_history:
        historical_polygon_client = PolygonHistoricalOptionsChainClient(
            settings=PolygonSettings.from_env()
        )

    results = []
    for symbol in symbols:
        result = backfill_symbol_history(
            symbol=symbol,
            historical_client=historical_client,
            lookback_days=args.lookback_days,
            dataset=dataset,
            schema=schema,
            db_path=db_path,
            source="databento",
            options_chain_provider=options_chain_provider,
            force_full_refresh=args.force_full_refresh,
        )

        historical_iv_rows_written = 0
        if historical_polygon_client is not None:
            historical_iv_rows_written = backfill_historical_iv_proxy_for_symbol(
                symbol=symbol,
                polygon_client=historical_polygon_client,
                db_path=db_path,
                limit=args.historical_iv_limit,
            )

        results.append(result)
        print(
            json.dumps(
                {
                    "symbol": result.symbol,
                    "bars_written": result.bars_written,
                    "iv_rows_written": result.iv_rows_written,
                    "historical_iv_rows_written": historical_iv_rows_written,
                    "feature_rows_written": result.feature_rows_written,
                    "latest_underlying_date": result.latest_underlying_date,
                    "latest_iv_date": result.latest_iv_date,
                    "latest_feature_date": result.latest_feature_date,
                },
                sort_keys=True,
            )
        )

    print(f"db_path={db_path}")
    print(f"dataset={dataset}")
    print(f"schema={schema}")
    print(f"symbols_processed={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
