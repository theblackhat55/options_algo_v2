from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from options_algo_v2.adapters.databento_live_historical_row_client import (
    DatabentoLiveHistoricalRowClient,
)
from options_algo_v2.domain.bar_data import BarData
from options_algo_v2.domain.historical_row_provider import HistoricalRowProvider
from options_algo_v2.services.databento_historical_fetcher import (
    fetch_databento_daily_rows,
)
from options_algo_v2.services.databento_settings import load_databento_settings
from options_algo_v2.services.history_store import (
    init_history_store,
    load_underlying_bars,
    upsert_underlying_bars,
)
from options_algo_v2.services.mock_historical_rows import build_mock_historical_rows
from options_algo_v2.services.runtime_mode import get_runtime_mode


DEFAULT_HISTORY_DB_PATH = "data/cache/market_history_watchlist60.db"
DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_SQLITE_MIN_ROWS = 60


def _load_live_databento_settings():
    return load_databento_settings()


def _get_historical_provider_mode() -> str:
    raw = os.getenv("OPTIONS_ALGO_HISTORICAL_PROVIDER_MODE", "").strip().lower()
    if raw in {"sqlite-first", "databento", "mock"}:
        return raw
    return "databento" if get_runtime_mode() == "live" else "mock"


def _get_history_db_path() -> Path:
    raw = os.getenv("OPTIONS_ALGO_HISTORY_DB_PATH", DEFAULT_HISTORY_DB_PATH).strip()
    return Path(raw)


def _get_lookback_days() -> int:
    raw = os.getenv("OPTIONS_ALGO_HISTORICAL_LOOKBACK_DAYS", str(DEFAULT_LOOKBACK_DAYS)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_LOOKBACK_DAYS
    return max(1, value)


def _get_sqlite_min_rows() -> int:
    raw = os.getenv("OPTIONS_ALGO_SQLITE_MIN_ROWS", str(DEFAULT_SQLITE_MIN_ROWS)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_SQLITE_MIN_ROWS
    return max(1, value)


def _rows_from_bars(bars: list[BarData]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for bar in bars:
        rows.append(
            {
                "ts_event": str(bar.timestamp),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(float(bar.volume)),
            }
        )
    return rows


def _bars_from_rows(rows: list[dict[str, object]]) -> list[BarData]:
    bars: list[BarData] = []
    for row in rows:
        ts_event = row.get("ts_event") or row.get("timestamp")
        if ts_event is None:
            continue
        try:
            bars.append(
                BarData(
                    timestamp=str(ts_event)[:10],
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return bars


@dataclass(frozen=True)
class MockHistoricalRowProvider(HistoricalRowProvider):
    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
        end_date: str | None = None,
    ) -> list[dict[str, object]]:
        _ = dataset
        _ = schema
        _ = end_date
        return build_mock_historical_rows(symbol=symbol)


@dataclass(frozen=True)
class DatabentoHistoricalRowProvider(HistoricalRowProvider):
    client: DatabentoLiveHistoricalRowClient
    source: str = "databento"

    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
        end_date: str | None = None,
    ) -> list[dict[str, object]]:
        return self.client.get_daily_rows(
            symbol=symbol,
            lookback_days=_get_lookback_days(),
            dataset=dataset,
            schema=schema,
            end_date=end_date,
        )


@dataclass(frozen=True)
class SQLiteFirstHistoricalRowProvider(HistoricalRowProvider):
    primary: DatabentoHistoricalRowProvider
    db_path: Path
    sqlite_min_rows: int
    source: str = "sqlite-first"

    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
        end_date: str | None = None,
    ) -> list[dict[str, object]]:
        _ = dataset
        _ = schema

        init_history_store(self.db_path)

        cached_bars = load_underlying_bars(
            symbol=symbol,
            end_date=end_date,
            db_path=self.db_path,
        )
        if len(cached_bars) >= self.sqlite_min_rows:
            return _rows_from_bars(cached_bars[-_get_lookback_days():])

        live_rows = self.primary.get_bar_rows(
            symbol=symbol,
            dataset=dataset,
            schema=schema,
            end_date=end_date,
        )
        if not live_rows:
            return _rows_from_bars(cached_bars[-_get_lookback_days():])

        fetched_bars = _bars_from_rows(live_rows)
        if fetched_bars:
            upsert_underlying_bars(
                symbol=symbol,
                bars=fetched_bars,
                db_path=self.db_path,
                source=self.primary.source,
            )

        refreshed_bars = load_underlying_bars(
            symbol=symbol,
            end_date=end_date,
            db_path=self.db_path,
        )
        if refreshed_bars:
            return _rows_from_bars(refreshed_bars[-_get_lookback_days():])

        return live_rows


def _build_databento_provider() -> DatabentoHistoricalRowProvider:
    settings = _load_live_databento_settings()
    return DatabentoHistoricalRowProvider(
        client=DatabentoLiveHistoricalRowClient(
            settings=settings,
            fetch_rows=fetch_databento_daily_rows,
        )
    )


def build_historical_row_provider() -> HistoricalRowProvider:
    runtime_mode = get_runtime_mode()
    provider_mode = _get_historical_provider_mode()

    if runtime_mode != "live":
        return MockHistoricalRowProvider()

    if provider_mode == "mock":
        return MockHistoricalRowProvider()

    if provider_mode == "sqlite-first":
        return SQLiteFirstHistoricalRowProvider(
            primary=_build_databento_provider(),
            db_path=_get_history_db_path(),
            sqlite_min_rows=_get_sqlite_min_rows(),
        )

    return _build_databento_provider()


def get_historical_row_provider_name() -> str:
    runtime_mode = get_runtime_mode()
    if runtime_mode != "live":
        return "mock"
    return _get_historical_provider_mode()


def get_historical_row_provider_source() -> str:
    runtime_mode = get_runtime_mode()
    if runtime_mode != "live":
        return "mock"

    provider_mode = _get_historical_provider_mode()
    if provider_mode == "sqlite-first":
        return str(_get_history_db_path())
    return provider_mode
