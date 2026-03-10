import pytest

from options_algo_v2.adapters.live_options_chain_client import (
    PolygonLiveOptionsChainClient,
)
from options_algo_v2.services.polygon_settings import PolygonSettings


def test_polygon_live_options_chain_client_stores_settings() -> None:
    client = PolygonLiveOptionsChainClient(
        settings=PolygonSettings(
            api_key="test-key",
            base_url="https://api.polygon.io",
        )
    )

    assert client.settings.api_key == "test-key"
    assert client.source == "polygon"


def test_polygon_live_options_chain_client_raises_not_implemented() -> None:
    client = PolygonLiveOptionsChainClient(
        settings=PolygonSettings(
            api_key="test-key",
            base_url="https://api.polygon.io",
        )
    )

    with pytest.raises(
        NotImplementedError,
        match="polygon live options chain client is not implemented",
    ):
        client.get_chain(symbol="AAPL")


def test_polygon_live_options_chain_client_normalizes_payload() -> None:
    client = PolygonLiveOptionsChainClient(
        settings=PolygonSettings(
            api_key="test-key",
            base_url="https://api.polygon.io",
        )
    )

    payload = {
        "as_of": "2026-03-10T21:00:00Z",
        "results": [
            {
                "details": {
                    "ticker": "O:AAPL260417C00145000",
                    "expiration_date": "2026-04-17",
                    "strike_price": 145.0,
                    "contract_type": "call",
                },
                "last_quote": {
                    "bid": 4.8,
                    "ask": 5.2,
                },
                "greeks": {
                    "delta": 0.42,
                },
                "open_interest": 1200,
                "day": {
                    "volume": 300,
                },
            }
        ],
    }

    snapshot = client.normalize_chain_payload(
        symbol="AAPL",
        payload=payload,
    )

    assert snapshot.symbol == "AAPL"
    assert snapshot.source == "polygon"
    assert snapshot.as_of == "2026-03-10T21:00:00Z"
    assert len(snapshot.quotes) == 1
    assert snapshot.quotes[0].option_symbol == "O:AAPL260417C00145000"
    assert snapshot.quotes[0].expiration == "2026-04-17"
    assert snapshot.quotes[0].strike == 145.0
    assert snapshot.quotes[0].option_type == "CALL"
    assert snapshot.quotes[0].bid == 4.8
    assert snapshot.quotes[0].ask == 5.2
    assert snapshot.quotes[0].mid == 5.0
    assert snapshot.quotes[0].delta == 0.42
    assert snapshot.quotes[0].open_interest == 1200
    assert snapshot.quotes[0].volume == 300


def test_polygon_live_options_chain_client_raises_for_invalid_results() -> None:
    client = PolygonLiveOptionsChainClient(
        settings=PolygonSettings(
            api_key="test-key",
            base_url="https://api.polygon.io",
        )
    )

    with pytest.raises(ValueError, match="results must be a list"):
        client.normalize_chain_payload(
            symbol="AAPL",
            payload={"results": "bad"},
        )
