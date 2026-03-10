import pytest

from options_algo_v2.services.runtime_mode import get_runtime_mode, is_mock_mode


def test_get_runtime_mode_defaults_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPTIONS_ALGO_RUNTIME_MODE", raising=False)

    assert get_runtime_mode() == "mock"
    assert is_mock_mode() is True


def test_get_runtime_mode_accepts_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")

    assert get_runtime_mode() == "mock"
    assert is_mock_mode() is True


def test_get_runtime_mode_accepts_live(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")

    assert get_runtime_mode() == "live"
    assert is_mock_mode() is False


def test_get_runtime_mode_rejects_invalid_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "paper")

    with pytest.raises(ValueError, match="OPTIONS_ALGO_RUNTIME_MODE"):
        get_runtime_mode()
