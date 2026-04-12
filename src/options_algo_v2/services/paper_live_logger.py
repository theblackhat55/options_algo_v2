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


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows

        if borderline_rescue_tier == "A" or borderline_score_pass_tier_a:
            borderline_score_pass = True
            borderline_score_pass_tier_a = True
            borderline_score_pass_tier_b = False
            borderline_rescue_tier = "A"
        elif borderline_rescue_tier == "B" or borderline_score_pass_tier_b:
            borderline_score_pass = True
            borderline_score_pass_tier_a = False
            borderline_score_pass_tier_b = True
            borderline_rescue_tier = "B"

        rows.append(json.loads(stripped))
    return rows


def _append_jsonl_if_missing(
    path: Path,
    row: dict[str, Any],
    *,
    key_fields: list[str],
) -> bool:
    _ensure_parent(path)
    existing_rows = _load_jsonl(path)

    for existing in existing_rows:
        if all(existing.get(field) == row.get(field) for field in key_fields):
            return False

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return True


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
        "options_context_matched_count": runtime_metadata.get("options_context_matched_count"),
        "options_context_missing_count": runtime_metadata.get("options_context_missing_count"),
        "options_context_regime_counts": runtime_metadata.get("options_context_regime_counts", {}),
        "options_context_low_confidence_symbols": runtime_metadata.get(
            "options_context_low_confidence_symbols", []
        ),
        "options_context_top_expected_move_symbols": runtime_metadata.get(
            "options_context_top_expected_move_symbols", []
        ),
        "options_context_top_skew_symbols": runtime_metadata.get(
            "options_context_top_skew_symbols", []
        ),
        "options_context_decision_adjusted_symbol_count": runtime_metadata.get(
            "options_context_decision_adjusted_symbol_count"
        ),
        "options_context_hard_reject_count": runtime_metadata.get(
            "options_context_hard_reject_count"
        ),
        "options_context_applied_reason_counts": runtime_metadata.get(
            "options_context_applied_reason_counts", {}
        ),
        "rejection_reason_counts": summary.get("rejection_reason_counts", {}),
        "signal_state_counts": summary.get("signal_state_counts", {}),
        "strategy_type_counts": summary.get("strategy_type_counts", {}),
    }


def build_symbol_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    runtime_metadata = payload.get("runtime_metadata", {}) or {}
    timestamp_utc = _utc_timestamp()
    run_id = payload.get("run_id")
    runtime_mode = runtime_metadata.get("runtime_mode")
    as_of_date = runtime_metadata.get("as_of_date")

    decisions = payload.get("decisions", []) or []
    feature_rows = runtime_metadata.get("feature_rows_by_symbol", {}) or {}
    trade_rows = runtime_metadata.get("top_trade_summary_rows_by_symbol", {}) or {}
    options_context_by_symbol = runtime_metadata.get("options_context_by_symbol", {}) or {}
    options_context_decision_debug_by_symbol = (
        runtime_metadata.get("options_context_decision_debug_by_symbol")
        or runtime_metadata.get("options_context_decision_debug")
        or {}
    )

    rows: list[dict[str, Any]] = []

    for decision in decisions:
        symbol = decision.get("symbol")
        feature_row = feature_rows.get(symbol, {}) or {}
        trace_row = trade_rows.get(symbol, {}) or {}
        options_context_row = options_context_by_symbol.get(symbol, {}) or {}
        options_context_decision_debug_row = (
            options_context_decision_debug_by_symbol.get(symbol, {}) or {}
        )

        borderline_score_pass = options_context_decision_debug_row.get(
            "borderline_score_pass"
        )
        borderline_score_pass_tier_a = options_context_decision_debug_row.get(
            "borderline_score_pass_tier_a"
        )
        borderline_score_pass_tier_b = options_context_decision_debug_row.get(
            "borderline_score_pass_tier_b"
        )
        borderline_rescue_tier = options_context_decision_debug_row.get(
            "borderline_rescue_tier"
        )

        if borderline_rescue_tier == "A" or borderline_score_pass_tier_a:
            borderline_score_pass = True
            borderline_score_pass_tier_a = True
            borderline_score_pass_tier_b = False
            borderline_rescue_tier = "A"
        elif borderline_rescue_tier == "B" or borderline_score_pass_tier_b:
            borderline_score_pass = True
            borderline_score_pass_tier_a = False
            borderline_score_pass_tier_b = True
            borderline_rescue_tier = "B"

        row = {
            "timestamp_utc": timestamp_utc,
            "run_id": run_id,
            "runtime_mode": runtime_mode,
            "as_of_date": as_of_date,
            "symbol": symbol,
            "final_passed": decision.get("final_passed"),
            "market_regime": decision.get("market_regime"),
            "directional_state": decision.get("directional_state"),
            "iv_state": decision.get("iv_state"),
            "signal_state": decision.get("signal_state"),
            "strategy_type": decision.get("strategy_type"),
            "final_score": decision.get("final_score"),
            "min_score_required": decision.get("min_score_required"),
            "blocking_reasons": decision.get("blocking_reasons", []),
            "soft_penalty_reasons": decision.get("soft_penalty_reasons", []),
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
            "options_context_available": options_context_row.get("context_available"),
            "options_context_source_provider": options_context_row.get("source_provider"),
            "options_context_as_of_utc": options_context_row.get("as_of_utc"),
            "options_contract_count": options_context_row.get("contract_count"),
            "options_expiration_count": options_context_row.get("expiration_count"),
            "options_pcr_oi": options_context_row.get("pcr_oi"),
            "options_pcr_volume": options_context_row.get("pcr_volume"),
            "options_atm_iv": options_context_row.get("atm_iv"),
            "options_expected_move_1d_pct": options_context_row.get("expected_move_1d_pct"),
            "options_expected_move_1w_pct": options_context_row.get("expected_move_1w_pct"),
            "options_expected_move_30d_pct": options_context_row.get("expected_move_30d_pct"),
            "options_skew_25d_put_call_ratio": options_context_row.get(
                "skew_25d_put_call_ratio"
            ),
            "options_skew_25d_put_call_spread": options_context_row.get(
                "skew_25d_put_call_spread"
            ),
            "options_nonzero_bid_ask_ratio": options_context_row.get(
                "nonzero_bid_ask_ratio"
            ),
            "options_nonzero_open_interest_ratio": options_context_row.get(
                "nonzero_open_interest_ratio"
            ),
            "options_nonzero_delta_ratio": options_context_row.get("nonzero_delta_ratio"),
            "options_nonzero_iv_ratio": options_context_row.get("nonzero_iv_ratio"),
            "options_summary_regime": options_context_row.get("options_summary_regime"),
            "options_confidence_score": options_context_row.get("confidence_score"),
            "options_context_reason_codes": options_context_decision_debug_row.get(
                "applied_reason_codes", []
            ),
            "options_context_advisory_reason_codes": options_context_decision_debug_row.get(
                "advisory_reason_codes", []
            ),
            "options_context_score_delta": options_context_decision_debug_row.get(
                "score_delta"
            ),
            "options_context_hard_reject": options_context_decision_debug_row.get(
                "hard_reject"
            ),
            "options_context_final_score_after_context": options_context_decision_debug_row.get(
                "final_score_after_context"
            ),
            "options_context_final_passed_after_context": options_context_decision_debug_row.get(
                "final_passed_after_context"
            ),
            "options_context_pre_context_score": options_context_decision_debug_row.get(
                "pre_context_score"
            ),
            "options_context_pre_context_score_gap": options_context_decision_debug_row.get(
                "pre_context_score_gap"
            ),
            "options_context_effective_soft_penalties": options_context_decision_debug_row.get(
                "effective_soft_penalties", []
            ),
            "options_context_borderline_score_pass": borderline_score_pass,
            "options_context_borderline_score_pass_tier_a": borderline_score_pass_tier_a,
            "options_context_borderline_score_pass_tier_b": borderline_score_pass_tier_b,
            "options_context_borderline_rescue_tier": borderline_rescue_tier,
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

    wrote_run = _append_jsonl_if_missing(
        resolved_paths.run_jsonl,
        run_row,
        key_fields=["run_id"],
    )
    for row in symbol_rows:
        _append_jsonl_if_missing(
            resolved_paths.symbol_jsonl,
            row,
            key_fields=["run_id", "symbol"],
        )

    if not wrote_run:
        return

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
        "options_context_matched_count": run_row["options_context_matched_count"],
        "options_context_missing_count": run_row["options_context_missing_count"],
        "options_context_regime_counts": _json_dict(run_row["options_context_regime_counts"]),
        "options_context_low_confidence_symbols": _json_list(
            run_row["options_context_low_confidence_symbols"]
        ),
        "options_context_top_expected_move_symbols": _json_list(
            run_row["options_context_top_expected_move_symbols"]
        ),
        "options_context_top_skew_symbols": _json_list(
            run_row["options_context_top_skew_symbols"]
        ),
        "options_context_decision_adjusted_symbol_count": run_row[
            "options_context_decision_adjusted_symbol_count"
        ],
        "options_context_hard_reject_count": run_row["options_context_hard_reject_count"],
        "options_context_applied_reason_counts": _json_dict(
            run_row["options_context_applied_reason_counts"]
        ),
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
            "options_context_matched_count",
            "options_context_missing_count",
            "options_context_regime_counts",
            "options_context_low_confidence_symbols",
            "options_context_top_expected_move_symbols",
            "options_context_top_skew_symbols",
            "options_context_decision_adjusted_symbol_count",
            "options_context_hard_reject_count",
            "options_context_applied_reason_counts",
            "rejection_reason_counts",
            "signal_state_counts",
            "strategy_type_counts",
        ],
    )
