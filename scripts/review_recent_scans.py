#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from collections import Counter, defaultdict
from pathlib import Path


def _load_scan(path: Path) -> dict:
    return json.loads(path.read_text())


def _iter_scan_files(limit: int, pattern: str) -> list[Path]:
    files = sorted(Path(p) for p in glob.glob(pattern))
    if limit > 0:
        files = files[-limit:]
    return files


def _score_gap(decision: dict) -> float | None:
    score = decision.get("final_score")
    minimum = decision.get("min_score_required")
    if score is None or minimum is None:
        return None
    try:
        return round(float(minimum) - float(score), 3)
    except (TypeError, ValueError):
        return None


def _is_borderline_failure(decision: dict) -> bool:
    if decision.get("final_passed"):
        return False
    blockers = set(decision.get("blocking_reasons") or [])
    gap = _score_gap(decision)
    return (
        blockers == {"candidate score below minimum threshold"}
        and gap is not None
        and 0.0 <= gap <= 5.0
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Review recent scan artifacts")
    parser.add_argument(
        "--pattern",
        default="data/scan_results/scan_*.json",
        help="Glob pattern for scan files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of most recent scan files to include",
    )
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=[],
        help="Optional symbol filter",
    )
    args = parser.parse_args()

    files = _iter_scan_files(limit=args.limit, pattern=args.pattern)
    if not files:
        raise SystemExit("no scan files found")

    symbol_filter = {s.upper() for s in args.symbols} if args.symbols else None

    per_symbol: dict[str, dict] = {}
    blocker_totals = Counter()
    soft_penalty_totals = Counter()
    repeated_borderline_failures = Counter()
    repeated_passed_with_soft_penalties = Counter()
    repeated_top_candidates = Counter()
    score_plus_soft_penalty_symbols = Counter()

    included_files: list[str] = []

    for path in files:
        data = _load_scan(path)
        included_files.append(path.name)
        runtime = data.get("runtime_metadata", {}) or {}

        for sym in runtime.get("top_trade_candidate_symbols", []) or []:
            if symbol_filter and sym.upper() not in symbol_filter:
                continue
            repeated_top_candidates[sym] += 1

        score_plus_summary = runtime.get("score_plus_soft_penalty_summary", {}) or {}
        for row in score_plus_summary.get("rows", []) or []:
            sym = row.get("symbol")
            if not sym:
                continue
            if symbol_filter and sym.upper() not in symbol_filter:
                continue
            score_plus_soft_penalty_symbols[sym] += 1

        for decision in data.get("decisions", []) or []:
            sym = (decision.get("symbol") or "").upper()
            if not sym:
                continue
            if symbol_filter and sym not in symbol_filter:
                continue

            entry = per_symbol.setdefault(
                sym,
                {
                    "appearances": 0,
                    "passes": 0,
                    "fails": 0,
                    "score_sum": 0.0,
                    "score_count": 0,
                    "gap_sum": 0.0,
                    "gap_count": 0,
                    "blocking_reason_counts": Counter(),
                    "soft_penalty_reason_counts": Counter(),
                },
            )

            entry["appearances"] += 1
            passed = bool(decision.get("final_passed"))
            if passed:
                entry["passes"] += 1
            else:
                entry["fails"] += 1

            score = decision.get("final_score")
            if score is not None:
                try:
                    entry["score_sum"] += float(score)
                    entry["score_count"] += 1
                except (TypeError, ValueError):
                    pass

            gap = _score_gap(decision)
            if gap is not None:
                entry["gap_sum"] += gap
                entry["gap_count"] += 1

            blocking = decision.get("blocking_reasons") or []
            soft = decision.get("soft_penalty_reasons") or []

            entry["blocking_reason_counts"].update(blocking)
            entry["soft_penalty_reason_counts"].update(soft)

            blocker_totals.update(blocking)
            soft_penalty_totals.update(soft)

            if _is_borderline_failure(decision):
                repeated_borderline_failures[sym] += 1

            if passed and soft:
                repeated_passed_with_soft_penalties[sym] += 1

    print("included_scan_files:")
    for name in included_files:
        print(" -", name)

    print("\nper_symbol_summary:")
    ranked_symbols = sorted(
        per_symbol.items(),
        key=lambda kv: (
            -kv[1]["passes"],
            -kv[1]["appearances"],
            -(kv[1]["score_sum"] / kv[1]["score_count"] if kv[1]["score_count"] else -9999),
            kv[0],
        ),
    )
    for sym, entry in ranked_symbols:
        avg_score = (
            round(entry["score_sum"] / entry["score_count"], 3)
            if entry["score_count"]
            else None
        )
        avg_gap = (
            round(entry["gap_sum"] / entry["gap_count"], 3)
            if entry["gap_count"]
            else None
        )
        print(
            {
                "symbol": sym,
                "appearances": entry["appearances"],
                "passes": entry["passes"],
                "fails": entry["fails"],
                "avg_final_score": avg_score,
                "avg_score_gap": avg_gap,
                "blocking_reason_counts": dict(entry["blocking_reason_counts"]),
                "soft_penalty_reason_counts": dict(entry["soft_penalty_reason_counts"]),
            }
        )

    print("\nglobal_blocking_reason_totals:")
    print(dict(blocker_totals))

    print("\nglobal_soft_penalty_reason_totals:")
    print(dict(soft_penalty_totals))

    print("\nrepeated_borderline_failures:")
    print(dict(repeated_borderline_failures))

    print("\nrepeated_passed_with_soft_penalties:")
    print(dict(repeated_passed_with_soft_penalties))

    print("\nrepeated_top_trade_candidates:")
    print(dict(repeated_top_candidates))

    print("\nscore_plus_soft_penalty_symbols:")
    print(dict(score_plus_soft_penalty_symbols))


if __name__ == "__main__":
    main()
