import pytest

from options_algo_v2.services.databento_historical_rows import (
    fetch_historical_bar_rows,
)


class FakeWrapper:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.calls: list[dict[str, object]] = []

    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> list[dict[str, object]]:
        self.calls.append(
            {
                "symbol": symbol,
                "dataset": dataset,
                "schema": schema,
            }
        )
        return self.rows


def test_fetch_historical_bar_rows_returns_rows() -> None:
    wrapper = FakeWrapper(
        rows=[
            {
                "ts_event": "2026-03-10T21:00:00Z",
                "open": 100.0,
                "high": 102.0,
                "low": 99.0,
                "close": 101.0,
                "volume": 1_000_000,
            }
        ]
    )

    rows = fetch_historical_bar_rows(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
        client_wrapper=wrapper,
    )

    assert len(rows) == 1
    assert rows[0]["close"] == 101.0
    assert wrapper.calls == [
        {
            "symbol": "AAPL",
            "dataset": "XNAS.ITCH",
            "schema": "ohlcv-1d",
        }
    ]


def test_fetch_historical_bar_rows_raises_when_empty() -> None:
    wrapper = FakeWrapper(rows=[])

    with pytest.raises(ValueError, match="no historical bar rows returned"):
        fetch_historical_bar_rows(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
            client_wrapper=wrapper,
        )
