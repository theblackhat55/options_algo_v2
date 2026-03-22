from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from options_algo_v2.domain.bar_data import BarData

DEFAULT_HISTORY_DB_PATH = Path("data/cache/market_history.db")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@contextmanager
def get_connection(db_path: Path = DEFAULT_HISTORY_DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_history_store(db_path: Path = DEFAULT_HISTORY_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS underlying_daily (
                symbol TEXT NOT NULL,
                as_of_date TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                source TEXT NOT NULL DEFAULT 'historical_provider',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (symbol, as_of_date)
            );

            CREATE TABLE IF NOT EXISTS iv_proxy_daily (
                symbol TEXT NOT NULL,
                as_of_date TEXT NOT NULL,
                implied_vol_proxy REAL NOT NULL,
                source TEXT NOT NULL DEFAULT 'polygon_near_atm',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (symbol, as_of_date)
            );

            CREATE TABLE IF NOT EXISTS feature_daily (
                symbol TEXT NOT NULL,
                as_of_date TEXT NOT NULL,
                close REAL NOT NULL,
                dma20 REAL,
                dma50 REAL,
                atr20 REAL,
                adx14 REAL,
                rsi14 REAL,
                five_day_return REAL,
                breakout_above_20d_high INTEGER NOT NULL DEFAULT 0,
                breakdown_below_20d_low INTEGER NOT NULL DEFAULT 0,
                breakout_volume_multiple REAL,
                avg_daily_volume REAL,
                hv20 REAL,
                iv_rank REAL,
                iv_hv_ratio REAL,
                feature_version TEXT NOT NULL,
                iv_method_version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (symbol, as_of_date)
            );

            CREATE TABLE IF NOT EXISTS cache_metadata (
                dataset TEXT NOT NULL,
                symbol TEXT NOT NULL,
                latest_date TEXT,
                row_count INTEGER NOT NULL DEFAULT 0,
                version TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (dataset, symbol)
            );

            CREATE INDEX IF NOT EXISTS idx_underlying_symbol_date
            ON underlying_daily (symbol, as_of_date);

            CREATE INDEX IF NOT EXISTS idx_iv_proxy_symbol_date
            ON iv_proxy_daily (symbol, as_of_date);

            CREATE INDEX IF NOT EXISTS idx_feature_symbol_date
            ON feature_daily (symbol, as_of_date);
            """
        )


def _bar_as_of_date(bar: BarData) -> str:
    return str(bar.timestamp)[:10]


def upsert_underlying_bars(
    *,
    symbol: str,
    bars: Iterable[BarData],
    db_path: Path = DEFAULT_HISTORY_DB_PATH,
    source: str = "historical_provider",
) -> int:
    rows = list(bars)
    if not rows:
        return 0

    now = utc_now_iso()
    payload = [
        (
            symbol,
            _bar_as_of_date(bar),
            float(bar.open),
            float(bar.high),
            float(bar.low),
            float(bar.close),
            float(bar.volume),
            source,
            now,
            now,
        )
        for bar in rows
    ]

    with get_connection(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO underlying_daily (
                symbol, as_of_date, open, high, low, close, volume,
                source, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, as_of_date) DO UPDATE SET
                open=excluded.open,
                high=excluded.high,
                low=excluded.low,
                close=excluded.close,
                volume=excluded.volume,
                source=excluded.source,
                updated_at=excluded.updated_at
            """,
            payload,
        )
    return len(payload)


def upsert_iv_proxy_rows(
    *,
    rows: Iterable[dict[str, object]],
    db_path: Path = DEFAULT_HISTORY_DB_PATH,
) -> int:
    payload_rows = list(rows)
    if not payload_rows:
        return 0

    now = utc_now_iso()
    payload = []
    for row in payload_rows:
        payload.append(
            (
                str(row["symbol"]),
                str(row["as_of_date"]),
                float(row["implied_vol_proxy"]),
                str(row.get("source", "polygon_near_atm")),
                now,
                now,
            )
        )

    with get_connection(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO iv_proxy_daily (
                symbol, as_of_date, implied_vol_proxy, source, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, as_of_date) DO UPDATE SET
                implied_vol_proxy=excluded.implied_vol_proxy,
                source=excluded.source,
                updated_at=excluded.updated_at
            """,
            payload,
        )
    return len(payload)


def upsert_feature_rows(
    *,
    rows: Iterable[dict[str, object]],
    db_path: Path = DEFAULT_HISTORY_DB_PATH,
) -> int:
    payload_rows = list(rows)
    if not payload_rows:
        return 0

    now = utc_now_iso()
    payload = []
    for row in payload_rows:
        payload.append(
            (
                str(row["symbol"]),
                str(row["as_of_date"]),
                float(row["close"]),
                row.get("dma20"),
                row.get("dma50"),
                row.get("atr20"),
                row.get("adx14"),
                row.get("rsi14"),
                row.get("five_day_return"),
                1 if row.get("breakout_above_20d_high") else 0,
                1 if row.get("breakdown_below_20d_low") else 0,
                row.get("breakout_volume_multiple"),
                row.get("avg_daily_volume"),
                row.get("hv20"),
                row.get("iv_rank"),
                row.get("iv_hv_ratio"),
                str(row.get("feature_version", "feature_v1")),
                str(row.get("iv_method_version", "atm_proxy_v1")),
                now,
                now,
            )
        )

    with get_connection(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO feature_daily (
                symbol, as_of_date, close, dma20, dma50, atr20, adx14, rsi14,
                five_day_return, breakout_above_20d_high, breakdown_below_20d_low,
                breakout_volume_multiple, avg_daily_volume, hv20, iv_rank, iv_hv_ratio,
                feature_version, iv_method_version, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, as_of_date) DO UPDATE SET
                close=excluded.close,
                dma20=excluded.dma20,
                dma50=excluded.dma50,
                atr20=excluded.atr20,
                adx14=excluded.adx14,
                rsi14=excluded.rsi14,
                five_day_return=excluded.five_day_return,
                breakout_above_20d_high=excluded.breakout_above_20d_high,
                breakdown_below_20d_low=excluded.breakdown_below_20d_low,
                breakout_volume_multiple=excluded.breakout_volume_multiple,
                avg_daily_volume=excluded.avg_daily_volume,
                hv20=excluded.hv20,
                iv_rank=excluded.iv_rank,
                iv_hv_ratio=excluded.iv_hv_ratio,
                feature_version=excluded.feature_version,
                iv_method_version=excluded.iv_method_version,
                updated_at=excluded.updated_at
            """,
            payload,
        )
    return len(payload)


def latest_cached_date(
    *,
    dataset: str,
    symbol: str,
    db_path: Path = DEFAULT_HISTORY_DB_PATH,
) -> str | None:
    table_map = {
        "underlying_daily": "underlying_daily",
        "iv_proxy_daily": "iv_proxy_daily",
        "feature_daily": "feature_daily",
    }
    table = table_map.get(dataset)
    if table is None:
        raise ValueError(f"unsupported dataset: {dataset}")

    with get_connection(db_path) as conn:
        row = conn.execute(
            f"SELECT MAX(as_of_date) FROM {table} WHERE symbol = ?",
            (symbol,),
        ).fetchone()
    if not row or not row[0]:
        return None
    return str(row[0])


def load_underlying_bars(
    *,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    db_path: Path = DEFAULT_HISTORY_DB_PATH,
) -> list[BarData]:
    query = """
        SELECT as_of_date, open, high, low, close, volume
        FROM underlying_daily
        WHERE symbol = ?
    """
    params: list[object] = [symbol]

    if start_date is not None:
        query += " AND as_of_date >= ?"
        params.append(start_date)
    if end_date is not None:
        query += " AND as_of_date <= ?"
        params.append(end_date)

    query += " ORDER BY as_of_date ASC"

    with get_connection(db_path) as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    return [
        BarData(
            timestamp=str(as_of_date),
            open=float(open_),
            high=float(high),
            low=float(low),
            close=float(close),
            volume=float(volume),
        )
        for as_of_date, open_, high, low, close, volume in rows
    ]


def load_iv_proxy_rows(
    *,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    db_path: Path = DEFAULT_HISTORY_DB_PATH,
) -> list[dict[str, object]]:
    query = """
        SELECT as_of_date, implied_vol_proxy, source
        FROM iv_proxy_daily
        WHERE symbol = ?
    """
    params: list[object] = [symbol]

    if start_date is not None:
        query += " AND as_of_date >= ?"
        params.append(start_date)
    if end_date is not None:
        query += " AND as_of_date <= ?"
        params.append(end_date)

    query += " ORDER BY as_of_date ASC"

    with get_connection(db_path) as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    return [
        {
            "symbol": symbol,
            "as_of_date": str(as_of_date),
            "implied_vol_proxy": float(implied_vol_proxy),
            "source": str(source),
        }
        for as_of_date, implied_vol_proxy, source in rows
    ]
