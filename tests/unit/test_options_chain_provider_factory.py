from __future__ import annotations

import pytest

from options_algo_v2.services.options_chain_provider_factory import (
    LiveOptionsChainProvider,
    MockOptionsChainProvider,
    build_options_chain_provider,
    get_options_chain_provider_name,
    get_options_chain_provider_source,
)


def test_build_options_chain_provider_returns_mock_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPTIONS_ALGO_RUNTIME_MODE", raising=False)

    provider = build_options_chain_provider()

    assert isinstance(provider, MockOptionsChainProvider)
    assert get_options_chain_provider_name() == "mock"
    assert get_options_chain_provider_source() == "mock"


def test_build_options_chain_provider_returns_mock_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    provider = build_options_chain_provider()

    assert isinstance(provider, MockOptionsChainProvider)


def test_build_options_chain_provider_live_mode_requires_polygon_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)

    with pytest.raises(
        ValueError,
        match="POLYGON_API_KEY is required for live options chain mode",
    ):
        build_options_chain_provider()


def test_build_options_chain_provider_returns_live_provider_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.setenv("POLYGON_API_KEY", "test-key")

    provider = build_options_chain_provider()

    assert isinstance(provider, LiveOptionsChainProvider)
    assert get_options_chain_provider_name() == "polygon"
    assert get_options_chain_provider_source() == "polygon"
