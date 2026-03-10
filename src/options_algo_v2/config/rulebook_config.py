from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path("config")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML config at {path}")
    return data


@dataclass(frozen=True)
class RulebookConfigSet:
    universe: dict[str, Any]
    strategy: dict[str, Any]
    risk: dict[str, Any]


def load_rulebook_configs(
    universe_file: str = "universe_v1.yaml",
    strategy_file: str = "strategy_v1.yaml",
    risk_file: str = "risk_v1.yaml",
) -> RulebookConfigSet:
    universe = _load_yaml(CONFIG_DIR / universe_file)
    strategy = _load_yaml(CONFIG_DIR / strategy_file)
    risk = _load_yaml(CONFIG_DIR / risk_file)

    return RulebookConfigSet(
        universe=universe,
        strategy=strategy,
        risk=risk,
    )
