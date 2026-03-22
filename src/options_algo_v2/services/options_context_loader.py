from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


def default_options_context_db_path(repo_root: Path | None = None) -> Path:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]
    return repo_root / os.getenv(
        "MARKET_HISTORY_DB_PATH",
        "data/cache/market_history_watchlist60.db",
    )


def load_options_context_payload(
    path: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    del path  # JSON fallback intentionally removed

    target = db_path or default_options_context_db_path()
    if not target.exists():
        return {
            "source": "sqlite",
            "db_path": str(target),
            "row_count": 0,
            "rows": [],
            "error": "options context sqlite db not found",
        }

    try:
        conn = sqlite3.connect(str(target))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT *
                FROM options_context_daily
                WHERE as_of_date = (
                    SELECT MAX(as_of_date) FROM options_context_daily
                )
                ORDER BY symbol
                """
            ).fetchall()
        finally:
            conn.close()
    except Exception as exc:
        return {
            "source": "sqlite",
            "db_path": str(target),
            "row_count": 0,
            "rows": [],
            "error": f"failed to load options_context_daily: {exc}",
        }

    payload_rows: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        for json_field in ("confidence_reasons_json", "missing_fields_json"):
            raw = item.get(json_field)
            if isinstance(raw, str):
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = []
            else:
                parsed = []

            if json_field == "confidence_reasons_json":
                item["confidence_reasons"] = parsed
            elif json_field == "missing_fields_json":
                item["missing_fields"] = parsed

        item.pop("confidence_reasons_json", None)
        item.pop("missing_fields_json", None)
        payload_rows.append(item)

    return {
        "source": "sqlite",
        "db_path": str(target),
        "row_count": len(payload_rows),
        "rows": payload_rows,
    }


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
