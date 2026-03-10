import pytest

from options_algo_v2.adapters.live_market_breadth_client import (
    PlaceholderLiveMarketBreadthClient,
)


def test_placeholder_live_market_breadth_client_stores_source() -> None:
    client = PlaceholderLiveMarketBreadthClient(source="breadth_stub")

    assert client.source == "breadth_stub"


def test_placeholder_live_market_breadth_client_raises_not_implemented() -> None:
    client = PlaceholderLiveMarketBreadthClient()

    with pytest.raises(
        NotImplementedError,
        match="live market breadth client is not implemented",
    ):
        client.get_market_breadth_snapshot()
