from __future__ import annotations

from options_algo_v2.adapters.databento_live_historical_row_client import (
    DatabentoLiveHistoricalRowClient,
)
from options_algo_v2.services.databento_settings import DatabentoSettings


def test_databento_live_historical_row_client_normalizes_rows() -> None:
    def fake_fetch_rows(
        symbol: str,
        lookback_days: int,
        dataset: str,
        schema: str,
        api_key: str,
        end_date: str | None = None,
    ) -> list[dict[str, object]]:
        assert symbol == "AAPL"
        assert lookback_days == 50
        assert dataset == "XNAS.ITCH"
        assert schema == "ohlcv-1d"
        assert api_key == "test-key"
        assert end_date is None
        return [
            {
                "timestamp": "2026-03-10T21:00:00Z",
                "open": "100.0",
                "high": 102.0,
                "low": 99.0,
                "close": "101.5",
                "volume": "1234567",
            },
            {
                "ts_event": "2026-03-11T21:00:00Z",
                "open": 101.5,
                "high": 103.0,
                "low": 100.5,
                "close": 102.0,
                "volume": 1239999,
            },
        ]

    client = DatabentoLiveHistoricalRowClient(
        settings=DatabentoSettings(
            api_key="test-key",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        ),
        fetch_rows=fake_fetch_rows,
    )

    rows = client.get_daily_rows(
        symbol="AAPL",
        lookback_days=50,
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )

    assert rows == [
        {
            "ts_event": "2026-03-10T21:00:00Z",
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.5,
            "volume": 1234567,
        },
        {
            "ts_event": "2026-03-11T21:00:00Z",
            "open": 101.5,
            "high": 103.0,
            "low": 100.5,
            "close": 102.0,
            "volume": 1239999,
        },
    ]


def test_databento_live_historical_row_client_skips_invalid_rows() -> None:
    def fake_fetch_rows(
        symbol: str,
        lookback_days: int,
        dataset: str,
        schema: str,
        api_key: str,
        end_date: str | None = None,
    ) -> list[dict[str, object]]:
        _ = symbol
        _ = lookback_days
        _ = dataset
        _ = schema
        _ = api_key
        _ = end_date
        return [
            {
                "timestamp": "2026-03-10T21:00:00Z",
                "open": "bad",
                "high": 102.0,
                "low": 99.0,
                "close": 101.5,
                "volume": 1234567,
            },
            {
                "timestamp": "2026-03-11T21:00:00Z",
                "open": 101.5,
                "high": 103.0,
                "low": 100.5,
                "close": 102.0,
                "volume": 1239999,
            },
        ]

    client = DatabentoLiveHistoricalRowClient(
        settings=DatabentoSettings(
            api_key="test-key",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        ),
        fetch_rows=fake_fetch_rows,
    )

    rows = client.get_daily_rows(
        symbol="AAPL",
        lookback_days=50,
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )

    assert len(rows) == 1
    assert rows[0]["ts_event"] == "2026-03-11T21:00:00Z"
