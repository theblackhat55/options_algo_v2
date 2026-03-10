import pytest

from options_algo_v2.services.databento_settings import (
    DatabentoSettings,
    load_databento_settings,
)


def test_load_databento_settings_returns_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")
    monkeypatch.delenv("DATABENTO_DATASET", raising=False)
    monkeypatch.delenv("DATABENTO_SCHEMA", raising=False)

    settings = load_databento_settings()

    assert settings == DatabentoSettings(
        api_key="test-key",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )


def test_load_databento_settings_uses_env_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "live-key")
    monkeypatch.setenv("DATABENTO_DATASET", "GLBX.MDP3")
    monkeypatch.setenv("DATABENTO_SCHEMA", "ohlcv-1m")

    settings = load_databento_settings()

    assert settings == DatabentoSettings(
        api_key="live-key",
        dataset="GLBX.MDP3",
        schema="ohlcv-1m",
    )


def test_load_databento_settings_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DATABENTO_API_KEY"):
        load_databento_settings()


def test_load_databento_settings_rejects_blank_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")
    monkeypatch.setenv("DATABENTO_DATASET", "   ")

    with pytest.raises(ValueError, match="DATABENTO_DATASET"):
        load_databento_settings()


def test_load_databento_settings_rejects_blank_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")
    monkeypatch.setenv("DATABENTO_SCHEMA", "   ")

    with pytest.raises(ValueError, match="DATABENTO_SCHEMA"):
        load_databento_settings()
