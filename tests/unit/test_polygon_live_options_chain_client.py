from __future__ import annotations

from options_algo_v2.adapters.polygon_live_options_chain_client import (
    PolygonLiveOptionsChainClient,
)


def test_polygon_live_options_chain_client_normalizes_snapshot(
    monkeypatch,
) -> None:
    monkeypatch.setenv("POLYGON_API_KEY", "test-key")

    captured: dict[str, object] = {}

    def fake_fetch_json(url: str, timeout_seconds: float) -> dict[str, object]:
        captured["url"] = url
        captured["timeout_seconds"] = timeout_seconds
        return {
            "request_id": "req-123",
            "results": [
                {
                    "details": {
                        "ticker": "O:AAPL260417C00100000",
                        "expiration_date": "2026-04-17",
                        "strike_price": 100,
                        "contract_type": "call",
                    },
                    "last_quote": {"bid": 2.4, "ask": 2.6},
                    "greeks": {"delta": 0.35},
                    "open_interest": 1500,
                    "day": {"volume": 250},
                },
                {
                    "details": {
                        "ticker": "O:AAPL260417P00095000",
                        "expiration_date": "2026-04-17",
                        "strike_price": "95",
                        "contract_type": "put",
                    },
                    "last_quote": {"bid": "1.4", "ask": "1.6"},
                    "greeks": {"delta": -0.22},
                    "open_interest": "1200",
                    "day": {"volume": "200"},
                },
            ],
        }

    client = PolygonLiveOptionsChainClient(fetch_json=fake_fetch_json)
    snapshot = client.get_chain_snapshot("AAPL")

    assert "underlying_ticker=AAPL" in str(captured["url"])
    assert captured["timeout_seconds"] == 10.0

    assert snapshot.symbol == "AAPL"
    assert snapshot.as_of == "req-123"
    assert snapshot.source == "polygon"
    assert len(snapshot.quotes) == 2

    first = snapshot.quotes[0]
    assert first.option_symbol == "O:AAPL260417C00100000"
    assert first.option_type == "CALL"
    assert first.bid == 2.4
    assert first.ask == 2.6
    assert first.mid == 2.5
    assert first.delta == 0.35
    assert first.open_interest == 1500
    assert first.volume == 250

    second = snapshot.quotes[1]
    assert second.option_type == "PUT"
    assert second.strike == 95.0
    assert second.mid == 1.5
    assert second.delta == -0.22


def test_polygon_live_options_chain_client_skips_invalid_entries(
    monkeypatch,
) -> None:
    monkeypatch.setenv("POLYGON_API_KEY", "test-key")

    def fake_fetch_json(_: str, __: float) -> dict[str, object]:
        return {
            "request_id": "req-456",
            "results": [
                {"details": {"ticker": "bad-no-quote"}},
                {
                    "details": {
                        "ticker": "O:AAPL260417C00100000",
                        "expiration_date": "2026-04-17",
                        "strike_price": 100,
                        "contract_type": "call",
                    },
                    "last_quote": {"bid": 2.4, "ask": 2.6},
                },
            ],
        }

    client = PolygonLiveOptionsChainClient(fetch_json=fake_fetch_json)
    snapshot = client.get_chain_snapshot("AAPL")

    assert len(snapshot.quotes) == 1
    assert snapshot.quotes[0].option_symbol == "O:AAPL260417C00100000"
