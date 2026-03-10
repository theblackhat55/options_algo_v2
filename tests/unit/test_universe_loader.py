import yaml

from options_algo_v2.services.universe_loader import load_universe_symbols


def test_load_universe_symbols_returns_uppercase_symbols(tmp_path) -> None:
    config_path = tmp_path / "universe.yaml"
    config_path.write_text(
        yaml.safe_dump({"version": "test", "symbols": ["aapl", "msft", "spy"]}),
        encoding="utf-8",
    )

    symbols = load_universe_symbols(config_path)

    assert symbols == ["AAPL", "MSFT", "SPY"]


def test_load_universe_symbols_raises_for_missing_symbols(tmp_path) -> None:
    config_path = tmp_path / "universe.yaml"
    config_path.write_text(
        yaml.safe_dump({"version": "test"}),
        encoding="utf-8",
    )

    try:
        load_universe_symbols(config_path)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "symbols list" in str(exc)
