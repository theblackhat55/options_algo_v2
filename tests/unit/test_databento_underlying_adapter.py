import pytest

from options_algo_v2.adapters.databento_underlying import (
    DatabentoUnderlyingAdapter,
)


def test_databento_underlying_adapter_returns_snapshot() -> None:
    def fake_fetcher(symbol: str) -> dict[str, object]:
        assert symbol == "AAPL"
        return {
            "close": 210.5,
            "volume": 1250000,
            "timestamp": "2026-03-10T21:00:00Z",
        }

    adapter = DatabentoUnderlyingAdapter(fetcher=fake_fetcher)
    snapshot = adapter.get_snapshot("AAPL")

    assert snapshot.symbol == "AAPL"
    assert snapshot.close == 210.5
    assert snapshot.volume == 1250000.0
    assert snapshot.timestamp == "2026-03-10T21:00:00Z"


def test_databento_underlying_adapter_raises_for_invalid_close() -> None:
    def fake_fetcher(symbol: str) -> dict[str, object]:
        return {
            "close": "bad",
            "volume": 1250000,
            "timestamp": "2026-03-10T21:00:00Z",
        }

    adapter = DatabentoUnderlyingAdapter(fetcher=fake_fetcher)

    with pytest.raises(ValueError, match="close must be numeric"):
        adapter.get_snapshot("AAPL")


def test_databento_underlying_adapter_raises_for_invalid_timestamp() -> None:
    def fake_fetcher(symbol: str) -> dict[str, object]:
        return {
            "close": 210.5,
            "volume": 1250000,
            "timestamp": 123,
        }

    adapter = DatabentoUnderlyingAdapter(fetcher=fake_fetcher)

    with pytest.raises(ValueError, match="timestamp must be a string"):
        adapter.get_snapshot("AAPL")
