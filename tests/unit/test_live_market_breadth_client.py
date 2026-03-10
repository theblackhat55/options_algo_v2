from __future__ import annotations

import pytest

from options_algo_v2.adapters.live_market_breadth_client import (
    LiveMarketBreadthClient,
)


def test_live_market_breadth_client_has_source() -> None:
    client = LiveMarketBreadthClient(
        fetch_payload=lambda: {
            "pct_above_20dma": 55.0,
            "timestamp": "2026-03-10T21:00:00Z",
        }
    )

    assert client.source == "market_breadth_live"


def test_live_market_breadth_client_normalizes_payload() -> None:
    client = LiveMarketBreadthClient(
        fetch_payload=lambda: {
            "pct_above_20dma": "58.5",
            "timestamp": "2026-03-10T21:00:00Z",
        }
    )

    snapshot = client.get_market_breadth_snapshot()

    assert snapshot.pct_above_20dma == 58.5
    assert snapshot.timestamp == "2026-03-10T21:00:00Z"
    assert snapshot.source == "market_breadth_live"


def test_live_market_breadth_client_requires_pct() -> None:
    client = LiveMarketBreadthClient(
        fetch_payload=lambda: {
            "timestamp": "2026-03-10T21:00:00Z",
        }
    )

    with pytest.raises(ValueError, match="pct_above_20dma is required"):
        client.get_market_breadth_snapshot()


def test_live_market_breadth_client_requires_timestamp() -> None:
    client = LiveMarketBreadthClient(
        fetch_payload=lambda: {
            "pct_above_20dma": 58.5,
        }
    )

    with pytest.raises(ValueError, match="timestamp is required"):
        client.get_market_breadth_snapshot()
