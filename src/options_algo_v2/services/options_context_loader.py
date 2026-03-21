from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_options_context_path(repo_root: Path | None = None) -> Path:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "data" / "validation" / "latest_options_context.json"


def load_options_context_payload(path: Path | None = None) -> dict[str, Any]:
    target = path or default_options_context_path()
    if not target.exists():
        return {}
    try:
        payload = json.loads(target.read_text())
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def build_options_context_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload.get("rows", [])
    index: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return index
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            continue
        index[symbol.strip().upper()] = row
    return index
