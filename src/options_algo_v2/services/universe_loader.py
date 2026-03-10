from __future__ import annotations

from pathlib import Path

import yaml


def load_universe_symbols(
    config_path: str | Path = "config/universe_v1.yaml",
) -> list[str]:
    path = Path(config_path)

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        msg = "universe config must be a mapping"
        raise ValueError(msg)

    symbols = data.get("symbols")
    if not isinstance(symbols, list):
        msg = "universe config must contain a symbols list"
        raise ValueError(msg)

    normalized = []
    for symbol in symbols:
        if not isinstance(symbol, str):
            msg = "all symbols must be strings"
            raise ValueError(msg)
        normalized.append(symbol.upper())

    return normalized
