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


def test_load_databento_module_raises_when_package_missing() -> None:
    sys.modules.pop("databento", None)

    with pytest.raises(RuntimeError, match="databento package is not installed"):
        _load_databento_module()


def test_build_get_range_kwargs_returns_expected_mapping() -> None:
    kwargs = _build_get_range_kwargs(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )

    assert kwargs == {
        "dataset": "XNAS.ITCH",
        "schema": "ohlcv-1d",
        "symbols": "AAPL",
        "stype_in": "raw_symbol",
        "limit": 100,
    }


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

    assert captured == {
        "dataset": "XNAS.ITCH",
        "schema": "ohlcv-1d",
        "symbols": "AAPL",
        "stype_in": "raw_symbol",
        "limit": 100,
    }


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

    with pytest.raises(ValueError, match="missing 'close'"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )


def test_databento_sdk_wrapper_raises_when_volume_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [{"close": 101.5, "ts_event": "2026-03-10T21:00:00Z"}]

    class FakeTimeseries:
        def get_range(self, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            self.timeseries = FakeTimeseries()

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")

    with pytest.raises(ValueError, match="missing 'volume'"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )


def test_databento_sdk_wrapper_raises_when_timestamp_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [{"close": 101.5, "volume": 1_000_000}]

    class FakeTimeseries:
        def get_range(self, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            self.timeseries = FakeTimeseries()

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")

    with pytest.raises(ValueError, match="missing 'ts_event'"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )


def test_databento_sdk_wrapper_raises_when_timestamp_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [{"close": 101.5, "volume": 1_000_000, "ts_event": "bad"}]

    class FakeTimeseries:
        def get_range(self, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            self.timeseries = FakeTimeseries()

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")

    with pytest.raises(ValueError, match="invalid 'ts_event' value"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )


def test_databento_sdk_wrapper_raises_when_close_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [
                {
                    "close": "bad",
                    "volume": 1_000_000,
                    "ts_event": "2026-03-10T21:00:00Z",
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

    with pytest.raises(ValueError, match="invalid 'close' value"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )


def test_databento_sdk_wrapper_raises_when_volume_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [
                {
                    "close": 101.5,
                    "volume": "bad",
                    "ts_event": "2026-03-10T21:00:00Z",
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

    with pytest.raises(ValueError, match="invalid 'volume' value"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )


def test_databento_sdk_wrapper_raises_when_close_non_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [
                {
                    "close": 0.0,
                    "volume": 1_000_000,
                    "ts_event": "2026-03-10T21:00:00Z",
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

    with pytest.raises(ValueError, match="close must be positive"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )


def test_databento_sdk_wrapper_raises_when_volume_negative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [
                {
                    "close": 101.5,
                    "volume": -1.0,
                    "ts_event": "2026-03-10T21:00:00Z",
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

    with pytest.raises(ValueError, match="volume cannot be negative"):
        wrapper.get_underlying_snapshot(
            symbol="AAPL",
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )


def test_databento_sdk_wrapper_get_bar_rows_returns_response_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def to_list(self) -> list[dict[str, object]]:
            return [
                {
                    "ts_event": "2026-03-10T21:00:00Z",
                    "open": 100.0,
                    "high": 102.0,
                    "low": 99.0,
                    "close": 101.0,
                    "volume": 1_000_000,
                }
            ]

    class FakeTimeseries:
        def get_range(self, **kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeHistorical:
        def __init__(self, api_key: str) -> None:
            self.timeseries = FakeTimeseries()

    import sys
    from types import SimpleNamespace

    fake_module = SimpleNamespace(Historical=FakeHistorical)
    monkeypatch.setitem(sys.modules, "databento", fake_module)

    wrapper = DatabentoHistoricalClientWrapper(api_key="test-key")
    rows = wrapper.get_bar_rows(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )

    assert rows == [
        {
            "ts_event": "2026-03-10T21:00:00Z",
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "volume": 1_000_000,
        }
    ]
