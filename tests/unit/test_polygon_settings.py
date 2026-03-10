from __future__ import annotations

import pytest

from options_algo_v2.services.polygon_settings import (
    get_polygon_api_key,
    get_polygon_base_url,
    get_polygon_timeout_seconds,
    has_polygon_api_key,
)


def test_get_polygon_api_key_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)

    with pytest.raises(
        ValueError,
        match="POLYGON_API_KEY is required for live options chain access",
    ):
        get_polygon_api_key()


def test_get_polygon_api_key_returns_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POLYGON_API_KEY", "test-polygon-key")

    assert get_polygon_api_key() == "test-polygon-key"


def test_has_polygon_api_key_reflects_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    assert has_polygon_api_key() is False

    monkeypatch.setenv("POLYGON_API_KEY", "abc")
    assert has_polygon_api_key() is True


def test_get_polygon_base_url_defaults_to_polygon(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POLYGON_BASE_URL", raising=False)

    assert get_polygon_base_url() == "https://api.polygon.io"


def test_get_polygon_timeout_seconds_defaults_to_ten(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POLYGON_TIMEOUT_SECONDS", raising=False)

    assert get_polygon_timeout_seconds() == 10.0
