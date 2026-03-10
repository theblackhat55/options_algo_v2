import pytest

from options_algo_v2.services.polygon_settings import load_polygon_settings


def test_load_polygon_settings_returns_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POLYGON_API_KEY", "test-key")
    monkeypatch.delenv("POLYGON_BASE_URL", raising=False)

    settings = load_polygon_settings()

    assert settings.api_key == "test-key"
    assert settings.base_url == "https://api.polygon.io"


def test_load_polygon_settings_raises_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)

    with pytest.raises(ValueError, match="POLYGON_API_KEY"):
        load_polygon_settings()


def test_load_polygon_settings_raises_when_base_url_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POLYGON_API_KEY", "test-key")
    monkeypatch.setenv("POLYGON_BASE_URL", "   ")

    with pytest.raises(ValueError, match="POLYGON_BASE_URL"):
        load_polygon_settings()
