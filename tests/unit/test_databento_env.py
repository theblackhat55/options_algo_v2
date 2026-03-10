import pytest

from options_algo_v2.services.databento_env import get_databento_api_key


def test_get_databento_api_key_returns_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "test-key")

    assert get_databento_api_key() == "test-key"


def test_get_databento_api_key_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DATABENTO_API_KEY"):
        get_databento_api_key()


def test_get_databento_api_key_raises_when_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "   ")

    with pytest.raises(ValueError, match="DATABENTO_API_KEY"):
        get_databento_api_key()
