import pytest

from options_algo_v2.domain.live_clients import UnderlyingLiveClient
from options_algo_v2.services.underlying_fetcher_factory import (
    build_underlying_fetcher,
)


class FakeLiveClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def get_underlying_snapshot(self, symbol: str) -> dict[str, object]:
        return {
            "close": 123.45,
            "volume": 9_999_999,
            "timestamp": "2026-03-10T21:00:00Z",
        }


def test_build_underlying_fetcher_returns_mock_fetcher_in_default_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPTIONS_ALGO_RUNTIME_MODE", raising=False)

    fetcher = build_underlying_fetcher()
    payload = fetcher("AAPL")

    assert payload["close"] == 210.0
    assert payload["volume"] == 5_000_000
    assert payload["timestamp"] == "2026-03-10T21:00:00Z"


def test_build_underlying_fetcher_returns_mock_fetcher_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    fetcher = build_underlying_fetcher()
    payload = fetcher("IBM")

    assert payload["close"] == 100.0
    assert payload["volume"] == 2_000_000
    assert payload["timestamp"] == "2026-03-10T21:00:00Z"


def test_build_underlying_fetcher_raises_when_live_mode_missing_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DATABENTO_API_KEY"):
        build_underlying_fetcher()


def test_build_underlying_fetcher_returns_live_callable_when_key_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")

    class MissingLiveClient:
        def __init__(self, api_key: str) -> None:
            self.api_key = api_key

        def get_underlying_snapshot(self, symbol: str) -> dict[str, object]:
            _ = symbol
            raise RuntimeError("databento package is not installed")

    def builder(api_key: str) -> UnderlyingLiveClient:
        return MissingLiveClient(api_key=api_key)

    fetcher = build_underlying_fetcher(client_builder=builder)

    with pytest.raises(RuntimeError, match="databento package is not installed"):
        fetcher("AAPL")


def test_build_underlying_fetcher_accepts_injected_live_client_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")

    def builder(api_key: str) -> UnderlyingLiveClient:
        return FakeLiveClient(api_key=api_key)

    fetcher = build_underlying_fetcher(client_builder=builder)
    payload = fetcher("AAPL")

    assert payload["close"] == 123.45
    assert payload["volume"] == 9_999_999
    assert payload["timestamp"] == "2026-03-10T21:00:00Z"
