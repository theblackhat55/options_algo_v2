from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RulebookConfigSet:
    universe: dict[str, Any]
    strategy: dict[str, Any]
    risk: dict[str, Any]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        msg = f"expected mapping at top level in {path}"
        raise ValueError(msg)

    return data


def load_rulebook_configs(config_dir: str | Path = "config") -> RulebookConfigSet:
    base_path = Path(config_dir)

    universe = _load_yaml(base_path / "universe_v1.yaml")
    strategy = _load_yaml(base_path / "strategy_v1.yaml")
    risk = _load_yaml(base_path / "risk_v1.yaml")

    return RulebookConfigSet(
        universe=universe,
        strategy=strategy,
        risk=risk,
    )
