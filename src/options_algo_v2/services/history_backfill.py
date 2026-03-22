from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from options_algo_v2.domain.bar_data import BarData
from options_algo_v2.domain.live_historical_row_client import LiveHistoricalRowClient
from options_algo_v2.domain.options_chain_provider import OptionsChainProvider
from options_algo_v2.services.feature_computation import compute_feature_rows_for_history
from options_algo_v2.services.iv_feature_estimator import estimate_near_atm_implied_vol
from options_algo_v2.services.history_store import (
    DEFAULT_HISTORY_DB_PATH,
    init_history_store,
    latest_cached_date,
    load_iv_proxy_rows,
    load_underlying_bars,
    upsert_feature_rows,
    upsert_iv_proxy_rows,
    upsert_underlying_bars,
)

DEFAULT_RECOMPUTE_BUFFER_DAYS = 70


@dataclass(frozen=True)
class BackfillResult:
    symbol: str
    bars_written: int
    iv_rows_written: int
    feature_rows_written: int
    latest_underlying_date: str | None
    latest_iv_date: str | None
    latest_feature_date: str | None


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _date_to_str(value: date) -> str:
    return value.isoformat()


def _subtract_days(value: str, days: int) -> str:
    return _date_to_str(_parse_date(value) - timedelta(days=days))


def _rows_to_bars(rows: list[dict[str, object]]) -> list[BarData]:
    bars: list[BarData] = []
    for row in rows:
        ts_event = row.get("ts_event") or row.get("timestamp")
        open_ = row.get("open")
        high = row.get("high")
        low = row.get("low")
        close = row.get("close")
        volume = row.get("volume")

        if ts_event is None:
            continue
        if not isinstance(open_, int | float):
            continue
        if not isinstance(high, int | float):
            continue
        if not isinstance(low, int | float):
            continue
        if not isinstance(close, int | float):
            continue
        if not isinstance(volume, int | float):
            continue

        bars.append(
            BarData(
                timestamp=str(ts_event),
                open=float(open_),
                high=float(high),
                low=float(low),
                close=float(close),
                volume=float(volume),
            )
        )
    return bars


def _get_bars_from_client(
    *,
    historical_client: object,
    symbol: str,
    lookback_days: int,
    dataset: str,
    schema: str,
) -> list[BarData]:
    get_daily_bars = getattr(historical_client, "get_daily_bars", None)
    if callable(get_daily_bars):
        return get_daily_bars(
            symbol=symbol,
            lookback_days=lookback_days,
            dataset=dataset,
            schema=schema,
        )

    get_daily_rows = getattr(historical_client, "get_daily_rows", None)
    if callable(get_daily_rows):
        rows = get_daily_rows(
            symbol=symbol,
            lookback_days=lookback_days,
            dataset=dataset,
            schema=schema,
        )
        return _rows_to_bars(rows)

    raise TypeError("historical_client must provide get_daily_bars(...) or get_daily_rows(...)")



def _maybe_build_latest_iv_proxy_row(
    *,
    symbol: str,
    bars: list[BarData],
    options_chain_provider: OptionsChainProvider | None,
) -> dict[str, object] | None:
    if options_chain_provider is None or not bars:
        return None

    latest_bar = bars[-1]
    underlying_price = float(latest_bar.close)
    as_of_date = str(latest_bar.timestamp)[:10]

    snapshot = options_chain_provider.get_chain(symbol=symbol)
    implied_vol_proxy = estimate_near_atm_implied_vol(
        snapshot=snapshot,
        underlying_price=underlying_price,
    )
    if implied_vol_proxy is None or implied_vol_proxy <= 0:
        return None

    return {
        "symbol": symbol,
        "as_of_date": as_of_date,
        "implied_vol_proxy": float(implied_vol_proxy),
        "source": snapshot.source or "polygon_near_atm",
    }

def backfill_symbol_history(
    *,
    symbol: str,
    historical_client: LiveHistoricalRowClient | object,
    lookback_days: int,
    dataset: str,
    schema: str,
    db_path: Path = DEFAULT_HISTORY_DB_PATH,
    source: str = "historical_provider",
    options_chain_provider: OptionsChainProvider | None = None,
    force_full_refresh: bool = False,
) -> BackfillResult:
    init_history_store(db_path)

    bars = _get_bars_from_client(
        historical_client=historical_client,
        symbol=symbol,
        lookback_days=lookback_days,
        dataset=dataset,
        schema=schema,
    )

    bars_written = upsert_underlying_bars(
        symbol=symbol,
        bars=bars,
        db_path=db_path,
        source=source,
    )

    latest_bar_date = latest_cached_date(
        dataset="underlying_daily",
        symbol=symbol,
        db_path=db_path,
    )

    iv_rows_written = 0
    latest_iv_row = _maybe_build_latest_iv_proxy_row(
        symbol=symbol,
        bars=bars,
        options_chain_provider=options_chain_provider,
    )
    if latest_iv_row is not None:
        iv_rows_written = upsert_iv_proxy_rows(
            rows=[latest_iv_row],
            db_path=db_path,
        )

    latest_iv_date = latest_cached_date(
        dataset="iv_proxy_daily",
        symbol=symbol,
        db_path=db_path,
    )

    if latest_bar_date is None:
        return BackfillResult(
            symbol=symbol,
            bars_written=bars_written,
            iv_rows_written=iv_rows_written,
            feature_rows_written=0,
            latest_underlying_date=None,
            latest_iv_date=latest_iv_date,
            latest_feature_date=None,
        )

    recompute_start = None
    if not force_full_refresh:
        existing_latest_feature = latest_cached_date(
            dataset="feature_daily",
            symbol=symbol,
            db_path=db_path,
        )
        if existing_latest_feature is not None:
            recompute_start = _subtract_days(existing_latest_feature, DEFAULT_RECOMPUTE_BUFFER_DAYS)

    cached_bars = load_underlying_bars(
        symbol=symbol,
        start_date=recompute_start,
        end_date=None,
        db_path=db_path,
    )

    iv_proxy_rows = load_iv_proxy_rows(
        symbol=symbol,
        start_date=recompute_start,
        end_date=None,
        db_path=db_path,
    )
    iv_proxy_by_date = {
        str(row["as_of_date"]): float(row["implied_vol_proxy"])
        for row in iv_proxy_rows
        if row.get("implied_vol_proxy") is not None
    }

    feature_rows = compute_feature_rows_for_history(
        symbol=symbol,
        bars=cached_bars,
        iv_proxy_by_date=iv_proxy_by_date,
    )
    feature_rows_written = upsert_feature_rows(
        rows=feature_rows,
        db_path=db_path,
    )

    latest_feature_date = latest_cached_date(
        dataset="feature_daily",
        symbol=symbol,
        db_path=db_path,
    )

    return BackfillResult(
        symbol=symbol,
        bars_written=bars_written,
        iv_rows_written=iv_rows_written,
        feature_rows_written=feature_rows_written,
        latest_underlying_date=latest_bar_date,
        latest_iv_date=latest_iv_date,
        latest_feature_date=latest_feature_date,
    )
