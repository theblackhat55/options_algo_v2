import pytest

from options_algo_v2.adapters.live_options_chain_client import (
    PlaceholderLiveOptionsChainClient,
)


def test_placeholder_live_options_chain_client_stores_source() -> None:
    client = PlaceholderLiveOptionsChainClient(source="options_stub")

    assert client.source == "options_stub"


def test_placeholder_live_options_chain_client_raises_not_implemented() -> None:
    client = PlaceholderLiveOptionsChainClient()

    with pytest.raises(
        NotImplementedError,
        match="live options chain client is not implemented",
    ):
        client.get_chain(symbol="AAPL")
