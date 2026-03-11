from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        rows.append(json.loads(stripped))
    return rows


def _safe_float(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _top_one(counter: Counter[str]) -> str | None:
    if not counter:
        return None
    return counter.most_common(1)[0][0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a symbol leaderboard from paper-live symbol logs."
    )
    parser.add_argument(
        "--validation-dir",
        type=str,
        default="data/validation",
        help="Directory containing paper_live_symbol_decisions.jsonl",
    )
    parser.add_argument(
        "--last-runs",
        type=int,
        default=None,
        help="Only include the most recent N run_ids present in symbol logs",
    )
    parser.add_argument(
        "--since-date",
        type=str,
        default=None,
        help="Only include rows with as_of_date >= YYYY-MM-DD",
    )
    parser.add_argument(
        "--sort-by",
        type=str,
        default="pass_rate",
        choices=[
            "pass_rate",
            "passes",
            "avg_score",
            "avg_adx14",
            "avg_iv_hv_ratio",
            "seen",
        ],
        help="Leaderboard sort key",
    )
    args = parser.parse_args()

    base = Path(args.validation_dir)
    rows = _load_jsonl(base / "paper_live_symbol_decisions.jsonl")

    if args.since_date is not None:
        rows = [
            row
            for row in rows
            if isinstance(row.get("as_of_date"), str)
            and row.get("as_of_date") >= args.since_date
        ]

    if args.last_runs is not None:
        ordered_run_ids: list[str] = []
        seen: set[str] = set()
        for row in rows:
            run_id = row.get("run_id")
            if isinstance(run_id, str) and run_id not in seen:
                seen.add(run_id)
                ordered_run_ids.append(run_id)
        keep_ids = set(ordered_run_ids[-args.last_runs :])
        rows = [
            row
            for row in rows
            if isinstance(row.get("run_id"), str) and row["run_id"] in keep_ids
        ]

    print(f"validation_dir={base}")
    print(f"row_count={len(rows)}")
    print(f"since_date={args.since_date}")
    print(f"last_runs={args.last_runs}")
    print(f"sort_by={args.sort_by}")

    if not rows:
        print("no symbol rows found")
        return 0

    seen_counter: Counter[str] = Counter()
    pass_counter: Counter[str] = Counter()
    directional_counter_by_symbol: dict[str, Counter[str]] = defaultdict(Counter)
    rejection_counter_by_symbol: dict[str, Counter[str]] = defaultdict(Counter)

    score_values: dict[str, list[float]] = defaultdict(list)
    adx_values: dict[str, list[float]] = defaultdict(list)
    iv_hv_values: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        symbol = row.get("symbol")
        if not isinstance(symbol, str):
            continue

        seen_counter[symbol] += 1
        if bool(row.get("final_passed")):
            pass_counter[symbol] += 1

        directional_state = row.get("directional_state")
        if isinstance(directional_state, str):
            directional_counter_by_symbol[symbol][directional_state] += 1

        for reason in row.get("rejection_reasons", []):
            if isinstance(reason, str):
                rejection_counter_by_symbol[symbol][reason] += 1

        score = _safe_float(row.get("final_score"))
        if score is not None:
            score_values[symbol].append(score)

        adx14 = _safe_float(row.get("adx14"))
        if adx14 is not None:
            adx_values[symbol].append(adx14)

        iv_hv_ratio = _safe_float(row.get("iv_hv_ratio"))
        if iv_hv_ratio is not None:
            iv_hv_values[symbol].append(iv_hv_ratio)

    leaderboard: list[dict[str, object]] = []

    for symbol, seen_count in seen_counter.items():
        passes = pass_counter[symbol]
        avg_score = _mean(score_values[symbol])
        avg_adx14 = _mean(adx_values[symbol])
        avg_iv_hv_ratio = _mean(iv_hv_values[symbol])

        leaderboard.append(
            {
                "symbol": symbol,
                "seen": seen_count,
                "passes": passes,
                "pass_rate": passes / seen_count if seen_count else 0.0,
                "avg_score": avg_score,
                "avg_adx14": avg_adx14,
                "avg_iv_hv_ratio": avg_iv_hv_ratio,
                "top_directional_state": _top_one(directional_counter_by_symbol[symbol]),
                "top_rejection_reason": _top_one(rejection_counter_by_symbol[symbol]),
            }
        )

    sort_key = args.sort_by
    leaderboard.sort(
        key=lambda row: (
            float(row[sort_key]) if isinstance(row[sort_key], int | float) else 0.0,
            float(row["passes"]) if isinstance(row["passes"], int | float) else 0.0,
            float(row["seen"]) if isinstance(row["seen"], int | float) else 0.0,
        ),
        reverse=True,
    )

    print("leaderboard:")
    for row in leaderboard:
        print(
            f"  {row['symbol']}: "
            f"seen={row['seen']} "
            f"passes={row['passes']} "
            f"pass_rate={float(row['pass_rate']):.4f} "
            f"avg_score={float(row['avg_score']):.2f} "
            f"avg_adx14={float(row['avg_adx14']):.2f} "
            f"avg_iv_hv_ratio={float(row['avg_iv_hv_ratio']):.4f} "
            f"top_directional_state={row['top_directional_state']} "
            f"top_rejection_reason={row['top_rejection_reason']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
