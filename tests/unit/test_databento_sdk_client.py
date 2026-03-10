import sys
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from options_algo_v2.adapters.databento_sdk_client import (
    DatabentoHistoricalClientWrapper,
    _build_get_range_kwargs,
    _load_databento_module,
)


def test_databento_sdk_wrapper_stores_api_key() -> None:
    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")

    assert wrapper.api_key == "test-key"


def test_load_databento_module_raises_when_package_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins

    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals: object = None,
        locals: object = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "databento":
            raise ImportError("No module named 'databento'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop("databento", None)

    with pytest.raises(RuntimeError, match="databento package is not installed"):
        _load_databento_module()


def test_build_get_range_kwargs_returns_expected_mapping() -> None:
    kwargs = _build_get_range_kwargs(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )

    assert kwargs["dataset"] == "XNAS.ITCH"
    assert kwargs["schema"] == "ohlcv-1d"
    assert kwargs["symbols"] == "AAPL"
    assert kwargs["stype_in"] == "raw_symbol"
    assert kwargs["limit"] == 100
    assert "start" in kwargs
    assert "end" in kwargs
    assert isinstance(kwargs["start"], datetime)
    assert isinstance(kwargs["end"], datetime)


def test_build_client_uses_databento_historical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_databento_sdk_wrapper_calls_get_range_with_expected_kwargs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [
                {
                    "close": 101.5,
                    "volume": 1_250_000,
                    "ts_event": "2026-03-10T21:00:00Z",
                }
            ]

    class FakeTimeseries:
        def get_range(self, **kwargs: object) -> FakeResponse:
            captured.update(kwargs)
            return FakeResponse()

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            self.timeseries = FakeTimeseries()

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")
    wrapper.get_underlying_snapshot(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )

    assert captured["dataset"] == "XNAS.ITCH"
    assert captured["schema"] == "ohlcv-1d"
    assert captured["symbols"] == "AAPL"
    assert captured["stype_in"] == "raw_symbol"
    assert captured["limit"] == 100
    assert "start" in captured
    assert "end" in captured
    assert isinstance(captured["start"], datetime)
    assert isinstance(captured["end"], datetime)


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


def test_databento_sdk_wrapper_normalizes_datetime_timestamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [
                {
                    "close": 101.5,
                    "volume": 1_250_000,
                    "ts_event": datetime(2026, 3, 10, 21, 0, tzinfo=UTC),
                }
            ]

    class FakeTimeseries:
        def get_range(self, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            self.timeseries = FakeTimeseries()

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")
    payload = wrapper.get_underlying_snapshot(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )

    assert payload["timestamp"] == "2026-03-10T21:00:00Z"


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


def test_databento_sdk_wrapper_raises_when_close_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [{"volume": 1_000_000, "ts_event": "2026-03-10T21:00:00Z"}]

    class FakeTimeseries:
        def get_range(self, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            self.timeseries = FakeTimeseries()

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")

    with pytest.raises(ValueError, match="missing 'close' in databento row"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )
