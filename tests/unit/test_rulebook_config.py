from options_algo_v2.config.rulebook_config import load_rulebook_configs


def test_load_rulebook_configs() -> None:
    configs = load_rulebook_configs()
    assert configs.universe["version"] == "universe_v1"
    assert configs.strategy["version"] == "strategy_v1"
    assert configs.risk["version"] == "risk_v1"


def test_universe_has_symbols() -> None:
    configs = load_rulebook_configs()
    symbols = configs.universe["symbols"]
    assert isinstance(symbols, list)
    assert "SPY" in symbols
    assert len(symbols) >= 10
