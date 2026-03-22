from __future__ import annotations

from pathlib import Path

from options_algo_v2.adapters.polygon_historical_options_chain_client import (
    PolygonHistoricalOptionsChainClient,
)
from options_algo_v2.services.history_store import (
    DEFAULT_HISTORY_DB_PATH,
    load_underlying_bars,
    upsert_iv_proxy_rows,
)
from options_algo_v2.services.iv_feature_estimator import estimate_near_atm_implied_vol


def backfill_historical_iv_proxy_for_symbol(
    *,
    symbol: str,
    polygon_client: PolygonHistoricalOptionsChainClient,
    db_path: Path = DEFAULT_HISTORY_DB_PATH,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 250,
) -> int:
    bars = load_underlying_bars(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        db_path=db_path,
    )

    rows_to_write: list[dict[str, object]] = []

    for bar in bars:
        as_of_date = str(bar.timestamp)[:10]
        snapshot = polygon_client.get_chain_snapshot(
            symbol=symbol,
            as_of_date=as_of_date,
            limit=limit,
        )
        implied_vol_proxy = estimate_near_atm_implied_vol(
            snapshot=snapshot,
            underlying_price=float(bar.close),
        )
        if implied_vol_proxy is None or implied_vol_proxy <= 0:
            continue

        rows_to_write.append(
            {
                "symbol": symbol,
                "as_of_date": as_of_date,
                "implied_vol_proxy": float(implied_vol_proxy),
                "source": snapshot.source,
            }
        )

    return upsert_iv_proxy_rows(rows=rows_to_write, db_path=db_path)
