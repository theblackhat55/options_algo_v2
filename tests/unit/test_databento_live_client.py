import pytest

from options_algo_v2.adapters.databento_live_client import DatabentoLiveClient


def test_databento_live_client_stores_api_key() -> None:
    client = DatabentoLiveClient(api_key="test-key")

    assert client.api_key == "test-key"


def test_databento_live_client_get_underlying_snapshot_not_implemented() -> None:
    client = DatabentoLiveClient(api_key="test-key")

    with pytest.raises(NotImplementedError, match="Databento live client"):
        client.get_underlying_snapshot("AAPL")
