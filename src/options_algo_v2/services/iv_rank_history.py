from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IvProxyObservation:
    as_of_date: str
    symbol: str
    implied_vol_proxy: float
    source: str = "polygon_near_atm"


def default_iv_rank_history_path(base_dir: str = "data/state") -> Path:
    return Path(base_dir) / "iv_proxy_history.jsonl"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_iv_proxy_history(path: Path) -> list[IvProxyObservation]:
    if not path.exists():
        return []

    rows: list[IvProxyObservation] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        as_of_date = payload.get("as_of_date")
        symbol = payload.get("symbol")
        implied_vol_proxy = payload.get("implied_vol_proxy")
        source = payload.get("source", "polygon_near_atm")

        if not isinstance(as_of_date, str) or not as_of_date:
            continue
        if not isinstance(symbol, str) or not symbol:
            continue
        if not isinstance(implied_vol_proxy, int | float):
            continue
        if not isinstance(source, str) or not source:
            continue

        rows.append(
            IvProxyObservation(
                as_of_date=as_of_date,
                symbol=symbol,
                implied_vol_proxy=float(implied_vol_proxy),
                source=source,
            )
        )
    return rows


def append_iv_proxy_observation(
    *,
    path: Path,
    observation: IvProxyObservation,
) -> bool:
    existing = load_iv_proxy_history(path)
    for row in existing:
        if row.as_of_date == observation.as_of_date and row.symbol == observation.symbol:
            return False

    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "as_of_date": observation.as_of_date,
                    "symbol": observation.symbol,
                    "implied_vol_proxy": observation.implied_vol_proxy,
                    "source": observation.source,
                },
                sort_keys=True,
            )
            + "\n"
        )
    return True


def count_iv_proxy_observations(*, path: Path, symbol: str) -> int:
    rows = load_iv_proxy_history(path)
    return sum(1 for row in rows if row.symbol == symbol)


def list_iv_proxy_observation_counts(path: Path) -> dict[str, int]:
    rows = load_iv_proxy_history(path)
    counts: Counter[str] = Counter(row.symbol for row in rows)
    return dict(counts)


def compute_iv_rank_from_history(
    *,
    path: Path,
    symbol: str,
    trailing_observations: int = 60,
) -> float | None:
    rows = load_iv_proxy_history(path)
    values = [
        row.implied_vol_proxy
        for row in rows
        if row.symbol == symbol and row.implied_vol_proxy > 0
    ]

    if len(values) < trailing_observations:
        return None

    window = values[-trailing_observations:]
    current = window[-1]
    iv_min = min(window)
    iv_max = max(window)

    if iv_max <= 0 or iv_min < 0:
        return None

    if iv_max == iv_min:
        return 50.0

    rank = 100.0 * (current - iv_min) / (iv_max - iv_min)
    if rank < 0:
        return 0.0
    if rank > 100:
        return 100.0
    return rank
