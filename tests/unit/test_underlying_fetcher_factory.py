import pytest

from options_algo_v2.services.underlying_fetcher_factory import (
    build_underlying_fetcher,
)


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


def test_build_underlying_fetcher_raises_in_live_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")

    with pytest.raises(NotImplementedError, match="live underlying fetcher"):
        build_underlying_fetcher()
