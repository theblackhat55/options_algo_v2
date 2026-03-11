from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PaperLiveLogPaths:
    run_jsonl: Path
    symbol_jsonl: Path
    run_csv: Path


def default_paper_live_log_paths(base_dir: str = "data/validation") -> PaperLiveLogPaths:
    root = Path(base_dir)
    return PaperLiveLogPaths(
        run_jsonl=root / "paper_live_runs.jsonl",
        symbol_jsonl=root / "paper_live_symbol_decisions.jsonl",
        run_csv=root / "paper_live_runs.csv",
    )


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_csv_row(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    _ensure_parent(path)
    file_exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _json_list(value: object) -> str:
    if isinstance(value, list):
        return json.dumps(value, sort_keys=True)
    return "[]"


def _json_dict(value: object) -> str:
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    return "{}"


def build_run_summary_row(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary", {})
    runtime_metadata = payload.get("runtime_metadata", {})

    return {
        "timestamp_utc": _utc_timestamp(),
        "run_id": payload.get("run_id"),
        "runtime_mode": runtime_metadata.get("runtime_mode"),
        "as_of_date": runtime_metadata.get("as_of_date"),
        "strict_live_mode": runtime_metadata.get("strict_live_mode"),
        "degraded_live_mode": runtime_metadata.get("degraded_live_mode"),
        "used_mock_historical_fallback": runtime_metadata.get(
            "used_mock_historical_fallback"
        ),
        "used_breadth_override": runtime_metadata.get("used_breadth_override"),
        "used_placeholder_iv_inputs": runtime_metadata.get(
            "used_placeholder_iv_inputs"
        ),
        "used_placeholder_iv_rank_inputs": runtime_metadata.get(
            "used_placeholder_iv_rank_inputs"
        ),
        "used_placeholder_iv_hv_ratio_inputs": runtime_metadata.get(
            "used_placeholder_iv_hv_ratio_inputs"
        ),
        "symbol_count": summary.get("total_candidates"),
        "passed_count": summary.get("total_passed"),
        "rejected_count": summary.get("total_rejected"),
        "passed_symbols": summary.get("passed_symbols", []),
        "rejected_symbols": summary.get("rejected_symbols", []),
        "top_trade_candidate_symbols": runtime_metadata.get(
            "top_trade_candidate_symbols", []
        ),
        "trade_idea_symbols": runtime_metadata.get("trade_idea_symbols", []),
        "rejection_reason_counts": summary.get("rejection_reason_counts", {}),
        "signal_state_counts": summary.get("signal_state_counts", {}),
        "strategy_type_counts": summary.get("strategy_type_counts", {}),
    }


def build_symbol_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    runtime_metadata = payload.get("runtime_metadata", {})
    feature_debug = runtime_metadata.get("feature_debug_by_symbol", {})
    decision_trace = runtime_metadata.get("decision_trace_by_symbol", {})

    rows: list[dict[str, Any]] = []
    for decision in payload.get("decisions", []):
        if not isinstance(decision, dict):
            continue

        symbol = decision.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            continue

        feature_row = feature_debug.get(symbol, {})
        trace_row = decision_trace.get(symbol, {})

        row = {
            "timestamp_utc": _utc_timestamp(),
            "run_id": payload.get("run_id"),
            "runtime_mode": runtime_metadata.get("runtime_mode"),
            "as_of_date": runtime_metadata.get("as_of_date"),
            "symbol": symbol,
            "final_passed": decision.get("final_passed"),
            "market_regime": decision.get("market_regime"),
            "directional_state": decision.get("directional_state"),
            "iv_state": decision.get("iv_state"),
            "signal_state": decision.get("signal_state"),
            "strategy_type": decision.get("strategy_type"),
            "final_score": decision.get("final_score"),
            "min_score_required": decision.get("min_score_required"),
            "rejection_reasons": decision.get("rejection_reasons", []),
            "rationale": decision.get("rationale", []),
            "close": decision.get("close"),
            "dma20": decision.get("dma20"),
            "dma50": decision.get("dma50"),
            "atr20": decision.get("atr20"),
            "adx14": decision.get("adx14"),
            "iv_rank": decision.get("iv_rank"),
            "iv_hv_ratio": decision.get("iv_hv_ratio"),
            "market_breadth_pct_above_20dma": decision.get(
                "market_breadth_pct_above_20dma"
            ),
            "directional_checks": decision.get("directional_checks", {}),
            "event_filter": decision.get("event_filter", {}),
            "extension_filter": decision.get("extension_filter", {}),
            "liquidity_filter": decision.get("liquidity_filter", {}),
            "feature_source_dataset": feature_row.get("dataset"),
            "feature_source_schema": feature_row.get("schema"),
            "historical_row_provider": feature_row.get("historical_row_provider"),
            "market_breadth_provider": feature_row.get("market_breadth_provider"),
            "trace_strategy_family": trace_row.get("strategy_family"),
        }
        rows.append(row)

    return rows


def append_paper_live_logs(
    *,
    payload: dict[str, Any],
    paths: PaperLiveLogPaths | None = None,
) -> None:
    resolved_paths = paths or default_paper_live_log_paths()

    run_row = build_run_summary_row(payload)
    symbol_rows = build_symbol_rows(payload)

    _append_jsonl(resolved_paths.run_jsonl, run_row)
    for row in symbol_rows:
        _append_jsonl(resolved_paths.symbol_jsonl, row)

    csv_row = {
        "timestamp_utc": run_row["timestamp_utc"],
        "run_id": run_row["run_id"],
        "runtime_mode": run_row["runtime_mode"],
        "as_of_date": run_row["as_of_date"],
        "strict_live_mode": run_row["strict_live_mode"],
        "degraded_live_mode": run_row["degraded_live_mode"],
        "used_placeholder_iv_inputs": run_row["used_placeholder_iv_inputs"],
        "used_placeholder_iv_rank_inputs": run_row["used_placeholder_iv_rank_inputs"],
        "used_placeholder_iv_hv_ratio_inputs": run_row[
            "used_placeholder_iv_hv_ratio_inputs"
        ],
        "symbol_count": run_row["symbol_count"],
        "passed_count": run_row["passed_count"],
        "rejected_count": run_row["rejected_count"],
        "passed_symbols": _json_list(run_row["passed_symbols"]),
        "rejected_symbols": _json_list(run_row["rejected_symbols"]),
        "top_trade_candidate_symbols": _json_list(
            run_row["top_trade_candidate_symbols"]
        ),
        "trade_idea_symbols": _json_list(run_row["trade_idea_symbols"]),
        "rejection_reason_counts": _json_dict(run_row["rejection_reason_counts"]),
        "signal_state_counts": _json_dict(run_row["signal_state_counts"]),
        "strategy_type_counts": _json_dict(run_row["strategy_type_counts"]),
    }

    _append_csv_row(
        resolved_paths.run_csv,
        csv_row,
        fieldnames=[
            "timestamp_utc",
            "run_id",
            "runtime_mode",
            "as_of_date",
            "strict_live_mode",
            "degraded_live_mode",
            "used_placeholder_iv_inputs",
            "used_placeholder_iv_rank_inputs",
            "used_placeholder_iv_hv_ratio_inputs",
            "symbol_count",
            "passed_count",
            "rejected_count",
            "passed_symbols",
            "rejected_symbols",
            "top_trade_candidate_symbols",
            "trade_idea_symbols",
            "rejection_reason_counts",
            "signal_state_counts",
            "strategy_type_counts",
        ],
    )
