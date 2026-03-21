from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def default_options_context_history_path() -> Path:
    return Path("data/state/options_context_history.jsonl")


def default_latest_options_context_path() -> Path:
    return Path("data/validation/latest_options_context.json")


def append_options_context_history(
    snapshots: list[Any],
    path: Path | None = None,
) -> Path:
    output_path = path or default_options_context_history_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as handle:
        for snapshot in snapshots:
            record = _to_serializable_dict(snapshot)
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    return output_path


def write_latest_options_context_snapshot(
    snapshots: list[Any],
    path: Path | None = None,
) -> Path:
    output_path = path or default_latest_options_context_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "row_count": len(snapshots),
        "rows": [_to_serializable_dict(snapshot) for snapshot in snapshots],
    }

    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def load_recent_options_context_history(
    path: Path | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    input_path = path or default_options_context_history_path()
    if not input_path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)

    if limit is not None and limit >= 0:
        return rows[-limit:]

    return rows


def _to_serializable_dict(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        payload = asdict(value)
    elif isinstance(value, dict):
        payload = dict(value)
    else:
        raise TypeError(f"unsupported snapshot type: {type(value)!r}")

    return payload
