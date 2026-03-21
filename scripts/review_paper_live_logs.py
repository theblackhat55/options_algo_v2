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


def _fmt_top(counter: Counter[str], limit: int = 10) -> list[tuple[str, int]]:
    return counter.most_common(limit)


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _filter_run_rows(
    rows: list[dict[str, Any]],
    *,
    since_date: str | None,
    last_runs: int | None,
) -> list[dict[str, Any]]:
    filtered = rows

    if since_date is not None:
        filtered = [
            row
            for row in filtered
            if isinstance(row.get("as_of_date"), str)
            and row.get("as_of_date") >= since_date
        ]

    if last_runs is not None:
        filtered = filtered[-last_runs:]

    return filtered


def _selected_run_ids(rows: list[dict[str, Any]]) -> set[str]:
    run_ids: set[str] = set()
    for row in rows:
        run_id = row.get("run_id")
        if isinstance(run_id, str) and run_id:
            run_ids.add(run_id)
    return run_ids


def _filter_symbol_rows(
    rows: list[dict[str, Any]],
    *,
    run_ids: set[str],
    symbol: str | None,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []

    for row in rows:
        run_id = row.get("run_id")
        if not isinstance(run_id, str) or run_id not in run_ids:
            continue

        if symbol is not None:
            row_symbol = row.get("symbol")
            if not isinstance(row_symbol, str) or row_symbol.upper() != symbol:
                continue

        filtered.append(row)

    return filtered


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review aggregated paper-live validation logs."
    )
    parser.add_argument(
        "--validation-dir",
        type=str,
        default="data/validation",
        help=(
            "Directory containing paper_live_runs.jsonl and "
            "paper_live_symbol_decisions.jsonl"
        ),
    )
    parser.add_argument(
        "--last-runs",
        type=int,
        default=None,
        help="Only include the most recent N runs",
    )
    parser.add_argument(
        "--since-date",
        type=str,
        default=None,
        help="Only include runs with as_of_date >= YYYY-MM-DD",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Only include symbol-level rows for a specific symbol",
    )
    args = parser.parse_args()

    symbol_filter = args.symbol.upper() if args.symbol else None

    base = Path(args.validation_dir)
    all_run_rows = _load_jsonl(base / "paper_live_runs.jsonl")
    all_symbol_rows = _load_jsonl(base / "paper_live_symbol_decisions.jsonl")

    run_rows = _filter_run_rows(
        all_run_rows,
        since_date=args.since_date,
        last_runs=args.last_runs,
    )
    run_ids = _selected_run_ids(run_rows)
    symbol_rows = _filter_symbol_rows(
        all_symbol_rows,
        run_ids=run_ids,
        symbol=symbol_filter,
    )

    print(f"validation_dir={base}")
    print(f"since_date={args.since_date}")
    print(f"last_runs={args.last_runs}")
    print(f"symbol_filter={symbol_filter}")
    print(f"run_count={len(run_rows)}")
    print(f"symbol_row_count={len(symbol_rows)}")

    if not run_rows:
        print("no run rows found")
        return 0

    total_symbols = 0
    total_passed = 0
    total_rejected = 0

    degraded_count = 0
    placeholder_iv_rank_count = 0
    placeholder_iv_hv_ratio_count = 0

    options_context_matched_total = 0
    options_context_missing_total = 0
    options_context_decision_adjusted_total = 0
    options_context_hard_reject_total = 0

    passed_symbol_counter: Counter[str] = Counter()
    top_trade_symbol_counter: Counter[str] = Counter()
    trade_idea_symbol_counter: Counter[str] = Counter()
    rejection_reason_counter: Counter[str] = Counter()
    signal_state_counter: Counter[str] = Counter()
    strategy_type_counter: Counter[str] = Counter()
    options_context_regime_counter: Counter[str] = Counter()
    options_context_applied_reason_counter: Counter[str] = Counter()

    for row in run_rows:
        total_symbols += int(row.get("symbol_count") or 0)
        total_passed += int(row.get("passed_count") or 0)
        total_rejected += int(row.get("rejected_count") or 0)

        if bool(row.get("degraded_live_mode")):
            degraded_count += 1
        if bool(row.get("used_placeholder_iv_rank_inputs")):
            placeholder_iv_rank_count += 1
        if bool(row.get("used_placeholder_iv_hv_ratio_inputs")):
            placeholder_iv_hv_ratio_count += 1

        options_context_matched_total += int(row.get("options_context_matched_count") or 0)
        options_context_missing_total += int(row.get("options_context_missing_count") or 0)
        options_context_decision_adjusted_total += int(
            row.get("options_context_decision_adjusted_symbol_count") or 0
        )
        options_context_hard_reject_total += int(
            row.get("options_context_hard_reject_count") or 0
        )

        for symbol in row.get("passed_symbols", []):
            if isinstance(symbol, str):
                passed_symbol_counter[symbol] += 1

        for symbol in row.get("top_trade_candidate_symbols", []):
            if isinstance(symbol, str):
                top_trade_symbol_counter[symbol] += 1

        for symbol in row.get("trade_idea_symbols", []):
            if isinstance(symbol, str):
                trade_idea_symbol_counter[symbol] += 1

        rejection_counts = row.get("rejection_reason_counts", {})
        if isinstance(rejection_counts, dict):
            for key, value in rejection_counts.items():
                if isinstance(key, str):
                    rejection_reason_counter[key] += int(value)

        signal_counts = row.get("signal_state_counts", {})
        if isinstance(signal_counts, dict):
            for key, value in signal_counts.items():
                if isinstance(key, str):
                    signal_state_counter[key] += int(value)

        strategy_counts = row.get("strategy_type_counts", {})
        if isinstance(strategy_counts, dict):
            for key, value in strategy_counts.items():
                if isinstance(key, str):
                    strategy_type_counter[key] += int(value)

        regime_counts = row.get("options_context_regime_counts", {})
        if isinstance(regime_counts, dict):
            for key, value in regime_counts.items():
                if isinstance(key, str):
                    options_context_regime_counter[key] += int(value)

        applied_reason_counts = row.get("options_context_applied_reason_counts", {})
        if isinstance(applied_reason_counts, dict):
            for key, value in applied_reason_counts.items():
                if isinstance(key, str):
                    options_context_applied_reason_counter[key] += int(value)

    print("run_summary:")
    print(f"  total_symbols_evaluated={total_symbols}")
    print(f"  total_passed={total_passed}")
    print(f"  total_rejected={total_rejected}")
    if total_symbols:
        print(f"  average_pass_rate={total_passed / total_symbols:.4f}")
    else:
        print("  average_pass_rate=0.0000")
    print(f"  degraded_live_run_count={degraded_count}")
    print(f"  placeholder_iv_rank_run_count={placeholder_iv_rank_count}")
    print(f"  placeholder_iv_hv_ratio_run_count={placeholder_iv_hv_ratio_count}")
    print(f"  options_context_matched_total={options_context_matched_total}")
    print(f"  options_context_missing_total={options_context_missing_total}")
    print(
        f"  options_context_decision_adjusted_total={options_context_decision_adjusted_total}"
    )
    print(f"  options_context_hard_reject_total={options_context_hard_reject_total}")

    print(f"top_passed_symbols={_fmt_top(passed_symbol_counter)}")
    print(f"top_trade_candidate_symbols={_fmt_top(top_trade_symbol_counter)}")
    print(f"top_trade_idea_symbols={_fmt_top(trade_idea_symbol_counter)}")
    print(f"rejection_reasons={_fmt_top(rejection_reason_counter)}")
    print(f"signal_states={_fmt_top(signal_state_counter)}")
    print(f"strategy_types={_fmt_top(strategy_type_counter)}")
    print(f"options_context_regimes={_fmt_top(options_context_regime_counter)}")
    print(
        "options_context_applied_reasons="
        f"{_fmt_top(options_context_applied_reason_counter)}"
    )

    if not symbol_rows:
        print("no symbol rows found")
        return 0

    symbol_counter: Counter[str] = Counter()
    symbol_pass_counter: Counter[str] = Counter()
    directional_state_counter: Counter[str] = Counter()
    market_regime_counter: Counter[str] = Counter()
    iv_state_counter: Counter[str] = Counter()
    symbol_rejection_counter: Counter[str] = Counter()
    options_summary_regime_counter: Counter[str] = Counter()
    options_context_reason_counter: Counter[str] = Counter()
    options_context_advisory_reason_counter: Counter[str] = Counter()
    options_penalized_symbol_counter: Counter[str] = Counter()
    confidence_by_symbol: dict[str, list[float]] = defaultdict(list)

    for row in symbol_rows:
        symbol = row.get("symbol")
        symbol_str = symbol if isinstance(symbol, str) else None

        if symbol_str is not None:
            symbol_counter[symbol_str] += 1
            if bool(row.get("final_passed")):
                symbol_pass_counter[symbol_str] += 1

        directional_state = row.get("directional_state")
        if isinstance(directional_state, str):
            directional_state_counter[directional_state] += 1

        market_regime = row.get("market_regime")
        if isinstance(market_regime, str):
            market_regime_counter[market_regime] += 1

        iv_state = row.get("iv_state")
        if isinstance(iv_state, str):
            iv_state_counter[iv_state] += 1

        for reason in row.get("rejection_reasons", []):
            if isinstance(reason, str):
                symbol_rejection_counter[reason] += 1

        options_summary_regime = row.get("options_summary_regime")
        if isinstance(options_summary_regime, str):
            options_summary_regime_counter[options_summary_regime] += 1

        options_confidence_score = row.get("options_confidence_score")
        if symbol_str is not None and isinstance(options_confidence_score, (int, float)):
            confidence_by_symbol[symbol_str].append(float(options_confidence_score))

        context_reason_codes = row.get("options_context_reason_codes", [])
        if isinstance(context_reason_codes, list):
            if symbol_str is not None and context_reason_codes:
                options_penalized_symbol_counter[symbol_str] += 1
            for reason in context_reason_codes:
                if isinstance(reason, str):
                    options_context_reason_counter[reason] += 1

        advisory_reason_codes = row.get("options_context_advisory_reason_codes", [])
        if isinstance(advisory_reason_codes, list):
            for reason in advisory_reason_codes:
                if isinstance(reason, str):
                    options_context_advisory_reason_counter[reason] += 1

    avg_confidence_rows: list[tuple[str, float]] = []
    for symbol, values in confidence_by_symbol.items():
        avg_value = _avg(values)
        if avg_value is not None:
            avg_confidence_rows.append((symbol, round(avg_value, 4)))
    avg_confidence_rows.sort(key=lambda item: item[1], reverse=True)

    print("symbol_summary:")
    print(f"  symbols_seen={_fmt_top(symbol_counter)}")
    print(f"  symbols_passed={_fmt_top(symbol_pass_counter)}")
    print(f"  directional_states={_fmt_top(directional_state_counter)}")
    print(f"  market_regimes={_fmt_top(market_regime_counter)}")
    print(f"  iv_states={_fmt_top(iv_state_counter)}")
    print(f"  symbol_rejection_reasons={_fmt_top(symbol_rejection_counter)}")
    print(f"  options_summary_regimes={_fmt_top(options_summary_regime_counter)}")
    print(f"  options_context_reason_codes={_fmt_top(options_context_reason_counter)}")
    print(
        f"  options_context_advisory_reason_codes={_fmt_top(options_context_advisory_reason_counter)}"
    )
    print(f"  options_penalized_symbols={_fmt_top(options_penalized_symbol_counter)}")
    print(f"  avg_options_confidence_by_symbol={avg_confidence_rows[:10]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
