import sys
from types import SimpleNamespace

import pytest

from options_algo_v2.adapters.databento_sdk_client import (
    DatabentoHistoricalClientWrapper,
    _load_databento_module,
)


def test_databento_sdk_wrapper_stores_api_key() -> None:
    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")

    assert wrapper.api_key == "test-key"


def test_load_databento_module_raises_when_package_missing() -> None:
    sys.modules.pop("databento", None)

    with pytest.raises(RuntimeError, match="databento package is not installed"):
        _load_databento_module()


def test_build_client_uses_databento_historical(monkeypatch: pytest.MonkeyPatch) -> None:
    created: dict[str, object] = {}

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            created["api_key"] = api_key

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="live-key")
    client = wrapper.build_client()

    assert isinstance(client, FakeHistorical)
    assert created["api_key"] == "live-key"


def test_databento_sdk_wrapper_parses_last_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [
                {
                    "close": 100.0,
                    "volume": 1_000_000,
                    "ts_event": "2026-03-10T20:59:00Z",
                },
                {
                    "close": 101.5,
                    "volume": 1_250_000,
                    "ts_event": "2026-03-10T21:00:00Z",
                },
            ]

    class FakeTimeseries:
        def get_range(self, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.timeseries = FakeTimeseries()

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")
    payload = wrapper.get_underlying_snapshot(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )

    assert payload == {
        "close": 101.5,
        "volume": 1_250_000.0,
        "timestamp": "2026-03-10T21:00:00Z",
    }


def test_databento_sdk_wrapper_raises_when_no_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return []

    class FakeTimeseries:
        def get_range(self, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key
            self.timeseries = FakeTimeseries()

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")

    with pytest.raises(ValueError, match="no databento rows returned"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )
