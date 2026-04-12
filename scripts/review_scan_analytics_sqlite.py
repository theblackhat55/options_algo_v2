#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from collections import Counter
from pathlib import Path


def _json_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _score_gap(row: dict[str, object]) -> float | None:
    score = row.get("final_score")
    minimum = row.get("min_score_required")
    if score is None or minimum is None:
        return None
    try:
        return round(float(minimum) - float(score), 3)
    except (TypeError, ValueError):
        return None


def _is_borderline_failure(row: dict[str, object]) -> bool:
    if bool(row.get("final_passed")):
        return False
    blockers = set(_json_list(row.get("blocking_reasons_json")))
    gap = _score_gap(row)
    return (
        blockers == {"candidate score below minimum threshold"}
        and gap is not None
        and 0.0 <= gap <= 5.0
    )


def _sorted_counter_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def _load_recent_run_rows(db_path: Path, limit_runs: int) -> list[dict[str, object]]:
    query = """
        SELECT
            run_id,
            timestamp_utc,
            runtime_mode,
            as_of_date,
            symbol_count,
            passed_count,
            rejected_count,
            top_trade_candidate_symbols_json
        FROM scan_run_summary
        ORDER BY timestamp_utc DESC
        LIMIT ?
    """
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, (limit_runs,)).fetchall()
    return [dict(row) for row in rows]


def _load_symbol_rows_for_runs(
    db_path: Path,
    run_ids: list[str],
) -> list[dict[str, object]]:
    if not run_ids:
        return []

    placeholders = ",".join("?" for _ in run_ids)
    query = f"""
        SELECT
            run_id,
            symbol,
            final_passed,
            final_score,
            min_score_required,
            strategy_type,
            directional_state,
            blocking_reasons_json,
            soft_penalty_reasons_json,
            rejection_reasons_json,
            options_summary_regime,
            options_context_borderline_score_pass,
            options_context_borderline_score_pass_tier_a,
            options_context_borderline_score_pass_tier_b,
            options_context_borderline_rescue_tier,
            options_context_pre_context_score,
            options_context_pre_context_score_gap,
            options_context_effective_soft_penalties_json
        FROM scan_symbol_decisions
        WHERE run_id IN ({placeholders})
    """
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, tuple(run_ids)).fetchall()
    return [dict(row) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Review recent scan analytics from SQLite")
    parser.add_argument(
        "--db-path",
        default=os.getenv("MARKET_HISTORY_DB_PATH", "data/cache/market_history_watchlist60.db"),
        help="SQLite DB path",
    )
    parser.add_argument(
        "--limit-runs",
        type=int,
        default=10,
        help="Number of most recent runs to include",
    )
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=[],
        help="Optional symbol filter",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path to write the review summary as JSON",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    if not db_path.exists():
        raise SystemExit(f"db path does not exist: {db_path}")

    run_rows = _load_recent_run_rows(db_path, args.limit_runs)
    if not run_rows:
        raise SystemExit("no scan_run_summary rows found")

    run_ids = [str(row["run_id"]) for row in run_rows]
    included_run_ids = list(run_ids)

    symbol_filter = {s.upper() for s in args.symbols} if args.symbols else None

    repeated_top_candidates = Counter()
    for row in run_rows:
        for sym in _json_list(row.get("top_trade_candidate_symbols_json")):
            sym_text = str(sym).upper()
            if symbol_filter and sym_text not in symbol_filter:
                continue
            repeated_top_candidates[sym_text] += 1

    symbol_rows = _load_symbol_rows_for_runs(db_path, run_ids)

    per_symbol: dict[str, dict[str, object]] = {}
    blocker_totals = Counter()
    soft_penalty_totals = Counter()
    repeated_borderline_failures = Counter()
    repeated_passed_with_soft_penalties = Counter()
    score_plus_soft_penalty_symbols = Counter()
    tier_a_rescue_counts_by_symbol = Counter()
    tier_b_rescue_counts_by_symbol = Counter()
    normal_pass_counts_by_symbol = Counter()
    rescued_pass_counts_by_symbol = Counter()

    for row in symbol_rows:
        sym = str(row.get("symbol") or "").upper()
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
                "pre_context_score_sum": 0.0,
                "pre_context_score_count": 0,
                "pre_context_gap_sum": 0.0,
                "pre_context_gap_count": 0,
                "score_uplift_sum": 0.0,
                "score_uplift_count": 0,
                "blocking_reason_counts": Counter(),
                "soft_penalty_reason_counts": Counter(),
            },
        )

        entry["appearances"] += 1
        passed = bool(row.get("final_passed"))
        if passed:
            entry["passes"] += 1
        else:
            entry["fails"] += 1

        score = row.get("final_score")
        if score is not None:
            try:
                entry["score_sum"] += float(score)
                entry["score_count"] += 1
            except (TypeError, ValueError):
                pass

        gap = _score_gap(row)
        if gap is not None:
            entry["gap_sum"] += gap
            entry["gap_count"] += 1

        pre_context_score = row.get("options_context_pre_context_score")
        if pre_context_score is not None:
            try:
                pre_context_score_value = float(pre_context_score)
                entry["pre_context_score_sum"] += pre_context_score_value
                entry["pre_context_score_count"] += 1

                final_score_value = row.get("final_score")
                if final_score_value is not None:
                    final_score_value = float(final_score_value)
                    entry["score_uplift_sum"] += round(
                        final_score_value - pre_context_score_value, 3
                    )
                    entry["score_uplift_count"] += 1
            except (TypeError, ValueError):
                pass

        pre_context_gap = row.get("options_context_pre_context_score_gap")
        if pre_context_gap is not None:
            try:
                entry["pre_context_gap_sum"] += float(pre_context_gap)
                entry["pre_context_gap_count"] += 1
            except (TypeError, ValueError):
                pass

        blocking = _json_list(row.get("blocking_reasons_json"))
        soft = _json_list(row.get("soft_penalty_reasons_json"))
        effective_soft = _json_list(row.get("options_context_effective_soft_penalties_json"))
        borderline_score_pass = bool(row.get("options_context_borderline_score_pass"))
        borderline_score_pass_tier_a = bool(row.get("options_context_borderline_score_pass_tier_a"))
        borderline_score_pass_tier_b = bool(row.get("options_context_borderline_score_pass_tier_b"))
        borderline_rescue_tier = str(row.get("options_context_borderline_rescue_tier") or "").upper()

        entry["blocking_reason_counts"].update(str(x) for x in blocking)
        entry["soft_penalty_reason_counts"].update(str(x) for x in soft)

        blocker_totals.update(str(x) for x in blocking)
        soft_penalty_totals.update(str(x) for x in soft)
        if effective_soft:
            soft_penalty_totals.update(str(x) for x in effective_soft)

        synthetic_row = {
            "final_passed": passed,
            "final_score": row.get("final_score"),
            "min_score_required": row.get("min_score_required"),
            "blocking_reasons_json": json.dumps(blocking, sort_keys=True),
        }
        if _is_borderline_failure(synthetic_row):
            repeated_borderline_failures[sym] += 1

        if passed and soft:
            repeated_passed_with_soft_penalties[sym] += 1

        if passed:
            if borderline_score_pass or borderline_rescue_tier in {"A", "B"}:
                rescued_pass_counts_by_symbol[sym] += 1
            else:
                normal_pass_counts_by_symbol[sym] += 1

            if borderline_score_pass_tier_a or borderline_rescue_tier == "A":
                tier_a_rescue_counts_by_symbol[sym] += 1

            if borderline_score_pass_tier_b or borderline_rescue_tier == "B":
                tier_b_rescue_counts_by_symbol[sym] += 1

        if (not passed) and ("candidate score below minimum threshold" in [str(x) for x in blocking]) and len(soft) > 0:
            score_plus_soft_penalty_symbols[sym] += 1

    ranked_symbols = sorted(
        per_symbol.items(),
        key=lambda kv: (
            -int(kv[1]["passes"]),
            -int(kv[1]["appearances"]),
            -(float(kv[1]["score_sum"]) / int(kv[1]["score_count"]) if kv[1]["score_count"] else -9999),
            kv[0],
        ),
    )

    per_symbol_rows = []
    for sym, entry in ranked_symbols:
        avg_score = (
            round(float(entry["score_sum"]) / int(entry["score_count"]), 3)
            if entry["score_count"]
            else None
        )
        avg_gap = (
            round(float(entry["gap_sum"]) / int(entry["gap_count"]), 3)
            if entry["gap_count"]
            else None
        )
        avg_pre_context_score = (
            round(float(entry["pre_context_score_sum"]) / int(entry["pre_context_score_count"]), 3)
            if entry["pre_context_score_count"]
            else None
        )
        avg_pre_context_gap = (
            round(float(entry["pre_context_gap_sum"]) / int(entry["pre_context_gap_count"]), 3)
            if entry["pre_context_gap_count"]
            else None
        )
        avg_score_uplift = (
            round(float(entry["score_uplift_sum"]) / int(entry["score_uplift_count"]), 3)
            if entry["score_uplift_count"]
            else None
        )
        per_symbol_rows.append(
            {
                "symbol": sym,
                "appearances": entry["appearances"],
                "passes": entry["passes"],
                "fails": entry["fails"],
                "avg_final_score": avg_score,
                "avg_score_gap": avg_gap,
                "avg_pre_context_score": avg_pre_context_score,
                "avg_pre_context_gap": avg_pre_context_gap,
                "avg_score_uplift": avg_score_uplift,
                "blocking_reason_counts": _sorted_counter_dict(entry["blocking_reason_counts"]),
                "soft_penalty_reason_counts": _sorted_counter_dict(entry["soft_penalty_reason_counts"]),
            }
        )

    summary = {
        "db_path": str(db_path),
        "included_run_ids": included_run_ids,
        "per_symbol_summary": per_symbol_rows,
        "global_blocking_reason_totals": _sorted_counter_dict(blocker_totals),
        "global_soft_penalty_reason_totals": _sorted_counter_dict(soft_penalty_totals),
        "repeated_borderline_failures": _sorted_counter_dict(repeated_borderline_failures),
        "repeated_passed_with_soft_penalties": _sorted_counter_dict(repeated_passed_with_soft_penalties),
        "repeated_top_trade_candidates": _sorted_counter_dict(repeated_top_candidates),
        "score_plus_soft_penalty_symbols": _sorted_counter_dict(score_plus_soft_penalty_symbols),
        "tier_a_rescue_counts_by_symbol": _sorted_counter_dict(tier_a_rescue_counts_by_symbol),
        "tier_b_rescue_counts_by_symbol": _sorted_counter_dict(tier_b_rescue_counts_by_symbol),
        "normal_pass_counts_by_symbol": _sorted_counter_dict(normal_pass_counts_by_symbol),
        "rescued_pass_counts_by_symbol": _sorted_counter_dict(rescued_pass_counts_by_symbol),
    }

    print(f"db_path: {summary['db_path']}")
    print("included_run_ids:")
    for run_id in summary["included_run_ids"]:
        print(" -", run_id)

    print("\nper_symbol_summary:")
    for row in summary["per_symbol_summary"]:
        print(row)

    print("\nglobal_blocking_reason_totals:")
    print(summary["global_blocking_reason_totals"])

    print("\nglobal_soft_penalty_reason_totals:")
    print(summary["global_soft_penalty_reason_totals"])

    print("\nrepeated_borderline_failures:")
    print(summary["repeated_borderline_failures"])

    print("\nrepeated_passed_with_soft_penalties:")
    print(summary["repeated_passed_with_soft_penalties"])

    print("\nrepeated_top_trade_candidates:")
    print(summary["repeated_top_trade_candidates"])

    print("\nscore_plus_soft_penalty_symbols:")
    print(summary["score_plus_soft_penalty_symbols"])

    print("\ntier_a_rescue_counts_by_symbol:")
    print(summary["tier_a_rescue_counts_by_symbol"])

    print("\ntier_b_rescue_counts_by_symbol:")
    print(summary["tier_b_rescue_counts_by_symbol"])

    print("\nnormal_pass_counts_by_symbol:")
    print(summary["normal_pass_counts_by_symbol"])

    print("\nrescued_pass_counts_by_symbol:")
    print(summary["rescued_pass_counts_by_symbol"])

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
        print(f"\njson_written_to: {out_path}")


if __name__ == "__main__":
    main()
