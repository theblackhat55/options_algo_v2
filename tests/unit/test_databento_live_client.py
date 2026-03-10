import pytest

from options_algo_v2.adapters.databento_live_client import DatabentoLiveClient


class FakeSdkWrapper:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get_underlying_snapshot(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "symbol": symbol,
                "dataset": dataset,
                "schema": schema,
            }
        )
        return {
            "close": 123.45,
            "volume": 1_234_567,
            "timestamp": "2026-03-10T21:00:00Z",
        }


def test_databento_live_client_stores_api_key() -> None:
    client = DatabentoLiveClient(api_key="test-key")

    assert client.api_key == "test-key"


def test_databento_live_client_delegates_to_sdk_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")
    monkeypatch.setenv("DATABENTO_DATASET", "XNAS.ITCH")
    monkeypatch.setenv("DATABENTO_SCHEMA", "ohlcv-1d")

    wrapper = FakeSdkWrapper()
    client = DatabentoLiveClient(api_key="test-key", sdk_wrapper=wrapper)

    payload = client.get_underlying_snapshot("AAPL")

    assert payload["close"] == 123.45
    assert payload["volume"] == 1_234_567
    assert payload["timestamp"] == "2026-03-10T21:00:00Z"
    assert wrapper.calls == [
        {
            "symbol": "AAPL",
            "dataset": "XNAS.ITCH",
            "schema": "ohlcv-1d",
        }
    ]


def test_databento_live_client_raises_when_package_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")
    monkeypatch.setenv("DATABENTO_DATASET", "XNAS.ITCH")
    monkeypatch.setenv("DATABENTO_SCHEMA", "ohlcv-1d")

    class MissingSdkWrapper:
        def get_underlying_snapshot(
            self,
            *,
            symbol: str,
            dataset: str,
            schema: str,
        ) -> dict[str, object]:
            _ = symbol
            _ = dataset
            _ = schema
            raise RuntimeError("databento package is not installed")

    client = DatabentoLiveClient(
        api_key="test-key",
        sdk_wrapper=MissingSdkWrapper(),
    )

    with pytest.raises(RuntimeError, match="databento package is not installed"):
        client.get_underlying_snapshot("AAPL")
