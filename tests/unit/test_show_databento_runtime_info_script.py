import pytest

from scripts.show_databento_runtime_info import show_databento_runtime_info


def test_show_databento_runtime_info_defaults(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    monkeypatch.delenv("DATABENTO_DATASET", raising=False)
    monkeypatch.delenv("DATABENTO_SCHEMA", raising=False)

    info = show_databento_runtime_info()
    captured = capsys.readouterr()

    assert info == {
        "dataset": "XNAS.ITCH",
        "schema": "ohlcv-1d",
        "has_api_key": "false",
    }
    assert "dataset=XNAS.ITCH" in captured.out
    assert "schema=ohlcv-1d" in captured.out
    assert "has_api_key=false" in captured.out


def test_show_databento_runtime_info_with_overrides(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "live-key")
    monkeypatch.setenv("DATABENTO_DATASET", "GLBX.MDP3")
    monkeypatch.setenv("DATABENTO_SCHEMA", "ohlcv-1m")

    info = show_databento_runtime_info()
    captured = capsys.readouterr()

    assert info == {
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1m",
        "has_api_key": "true",
    }
    assert "dataset=GLBX.MDP3" in captured.out
    assert "schema=ohlcv-1m" in captured.out
    assert "has_api_key=true" in captured.out
