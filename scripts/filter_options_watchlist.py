from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


LATEST_OPTIONS_CONTEXT_PATH = Path("data/validation/latest_options_context.json")


def _parse_args(argv: list[str]) -> tuple[Path, int | None]:
    if not argv:
        raise SystemExit(
            "usage: PYTHONPATH=src python scripts/filter_options_watchlist.py "
            "data/watchlists/options_watchlist_<run_id>.json [--top-n N]"
        )

    source_path = Path(argv[0])
    top_n: int | None = None

    if len(argv) >= 3 and argv[1] == "--top-n":
        try:
            top_n = int(argv[2])
        except ValueError as exc:
            raise SystemExit("--top-n requires an integer") from exc

        if top_n <= 0:
            raise SystemExit("--top-n must be positive")

    return source_path, top_n


def _load_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text())
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise RuntimeError("watchlist rows must be a list")
    return [row for row in rows if isinstance(row, dict)]


def _load_latest_options_context(
    path: Path = LATEST_OPTIONS_CONTEXT_PATH,
) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}

    payload = json.loads(path.read_text())
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return {}

    by_symbol: dict[str, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            continue
        by_symbol[symbol.strip().upper()] = row
    return by_symbol


def _enrich_row_with_options_context(
    row: dict[str, object],
    context_by_symbol: dict[str, dict[str, object]],
) -> dict[str, object]:
    enriched = dict(row)
    symbol = str(row.get("symbol", "")).strip().upper()
    context = context_by_symbol.get(symbol, {})

    field_names = [
        "expected_move_1d_pct",
        "expected_move_1w_pct",
        "expected_move_30d_pct",
        "skew_25d_put_call_ratio",
        "skew_25d_put_call_spread",
        "pcr_oi",
        "pcr_volume",
        "confidence_score",
        "confidence_reasons",
        "missing_fields",
        "source_provider",
    ]

    for field_name in field_names:
        if field_name in context:
            enriched[field_name] = context[field_name]

    if "confidence_score" in enriched:
        enriched["options_context_confidence"] = enriched.get("confidence_score")

    if context:
        enriched["options_context_available"] = True
    else:
        enriched["options_context_available"] = False
        enriched.setdefault("expected_move_1d_pct", None)
        enriched.setdefault("expected_move_1w_pct", None)
        enriched.setdefault("expected_move_30d_pct", None)
        enriched.setdefault("skew_25d_put_call_ratio", None)
        enriched.setdefault("skew_25d_put_call_spread", None)
        enriched.setdefault("pcr_oi", None)
        enriched.setdefault("pcr_volume", None)
        enriched.setdefault("options_context_confidence", None)
        enriched.setdefault("confidence_reasons", [])
        enriched.setdefault("missing_fields", [])

    return enriched


def filter_options_watchlist(source_path: str, top_n: int | None = None) -> str:
    path = Path(source_path)
    rows = _load_rows(path)
    context_by_symbol = _load_latest_options_context()

    viable_rows = [
        _enrich_row_with_options_context(row, context_by_symbol)
        for row in rows
        if bool(row.get("options_viable", False))
    ]

    viable_rows.sort(
        key=lambda row: float(row.get("combined_score", 0.0)),
        reverse=True,
    )

    if top_n is not None:
        viable_rows = viable_rows[:top_n]

    run_id = "options_watchlist_filtered_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path("data/watchlists")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{run_id}.json"

    payload = {
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source_watchlist_path": str(path),
        "top_n": top_n,
        "row_count": len(viable_rows),
        "rows": viable_rows,
    }

    output_path.write_text(json.dumps(payload, indent=2))

    top_symbols = [row.get("symbol") for row in viable_rows[:10]]

    context_coverage = sum(
        1 for row in viable_rows if bool(row.get("options_context_available", False))
    )

    print(f"source_watchlist_path={path}")
    print(f"top_n={top_n}")
    print(f"row_count={len(viable_rows)}")
    print(f"options_context_coverage={context_coverage}/{len(viable_rows) if viable_rows else 0}")
    print(f"output_path={output_path}")
    print(f"top_filtered_symbols={top_symbols}")

    return str(output_path)


if __name__ == "__main__":
    parsed_path, parsed_top_n = _parse_args(sys.argv[1:])
    filter_options_watchlist(str(parsed_path), top_n=parsed_top_n)
