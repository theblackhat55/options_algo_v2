import pytest

from options_algo_v2.services.databento_runtime_info import (
    build_databento_runtime_info,
)


def test_build_databento_runtime_info_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    monkeypatch.delenv("DATABENTO_DATASET", raising=False)
    monkeypatch.delenv("DATABENTO_SCHEMA", raising=False)

    info = build_databento_runtime_info()

    assert info == {
        "dataset": "XNAS.ITCH",
        "schema": "ohlcv-1d",
        "has_api_key": "false",
    }


def test_build_databento_runtime_info_with_api_key_and_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "live-key")
    monkeypatch.setenv("DATABENTO_DATASET", "GLBX.MDP3")
    monkeypatch.setenv("DATABENTO_SCHEMA", "ohlcv-1m")

    info = build_databento_runtime_info()

    assert info == {
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1m",
        "has_api_key": "true",
    }
