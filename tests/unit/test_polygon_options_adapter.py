import pytest

from options_algo_v2.adapters.polygon_options import PolygonOptionsAdapter


def test_polygon_options_adapter_returns_snapshot() -> None:
    def fake_fetcher(option_symbol: str) -> dict[str, object]:
        assert option_symbol == "O:AAPL260320C00210000"
        return {
            "underlying_symbol": "AAPL",
            "strike": 210.0,
            "right": "C",
            "expiry": "2026-03-20",
            "bid": 2.40,
            "ask": 2.55,
            "iv": 0.28,
            "delta": 0.42,
            "open_interest": 1250,
            "volume": 340,
            "quote_timestamp": "2026-03-10T20:59:00Z",
        }

    adapter = PolygonOptionsAdapter(fetcher=fake_fetcher)
    snapshot = adapter.get_snapshot("O:AAPL260320C00210000")

    assert snapshot.underlying_symbol == "AAPL"
    assert snapshot.option_symbol == "O:AAPL260320C00210000"
    assert snapshot.strike == 210.0
    assert snapshot.right == "C"
    assert snapshot.expiry == "2026-03-20"
    assert snapshot.bid == 2.40
    assert snapshot.ask == 2.55
    assert snapshot.iv == 0.28
    assert snapshot.delta == 0.42
    assert snapshot.open_interest == 1250
    assert snapshot.volume == 340
    assert snapshot.quote_timestamp == "2026-03-10T20:59:00Z"


def test_polygon_options_adapter_raises_for_invalid_right() -> None:
    def fake_fetcher(option_symbol: str) -> dict[str, object]:
        return {
            "underlying_symbol": "AAPL",
            "strike": 210.0,
            "right": "X",
            "expiry": "2026-03-20",
            "bid": 2.40,
            "ask": 2.55,
            "iv": 0.28,
            "delta": 0.42,
            "open_interest": 1250,
            "volume": 340,
            "quote_timestamp": "2026-03-10T20:59:00Z",
        }

    adapter = PolygonOptionsAdapter(fetcher=fake_fetcher)

    with pytest.raises(ValueError, match="right must be C or P"):
        adapter.get_snapshot("O:AAPL260320C00210000")


def test_polygon_options_adapter_raises_for_invalid_iv() -> None:
    def fake_fetcher(option_symbol: str) -> dict[str, object]:
        return {
            "underlying_symbol": "AAPL",
            "strike": 210.0,
            "right": "C",
            "expiry": "2026-03-20",
            "bid": 2.40,
            "ask": 2.55,
            "iv": "bad",
            "delta": 0.42,
            "open_interest": 1250,
            "volume": 340,
            "quote_timestamp": "2026-03-10T20:59:00Z",
        }

    adapter = PolygonOptionsAdapter(fetcher=fake_fetcher)

    with pytest.raises(ValueError, match="iv must be numeric"):
        adapter.get_snapshot("O:AAPL260320C00210000")
