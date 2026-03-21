from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_latest_scan(scan_dir: Path) -> tuple[Path | None, dict[str, Any] | None]:
    files = sorted(scan_dir.glob("scan_*.json"))
    if not files:
        return None, None
    latest = files[-1]
    try:
        payload = json.loads(latest.read_text())
        if not isinstance(payload, dict):
            return latest, None
        return latest, payload
    except Exception:
        return latest, None


def _load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _load_last_jsonl_row(path: Path) -> dict[str, Any] | None:
    rows = _load_jsonl_rows(path)
    if not rows:
        return None
    return rows[-1]


def _find_run_row_by_run_id(path: Path, run_id: str | None) -> dict[str, Any] | None:
    if not run_id:
        return None
    for row in reversed(_load_jsonl_rows(path)):
        if row.get("run_id") == run_id:
            return row
    return None


def _primary_degradation_cause(runtime_metadata: dict[str, Any]) -> str | None:
    if runtime_metadata.get("used_placeholder_iv_rank_inputs"):
        return "placeholder IV rank inputs"
    if runtime_metadata.get("used_placeholder_iv_hv_ratio_inputs"):
        return "placeholder IV/HV ratio inputs"
    if runtime_metadata.get("used_placeholder_liquidity_inputs"):
        return "placeholder liquidity inputs"
    if runtime_metadata.get("used_mock_historical_fallback"):
        return "mock historical fallback"
    if runtime_metadata.get("used_breadth_override"):
        return "breadth override"
    if runtime_metadata.get("degraded_live_mode"):
        return "unknown degraded live mode cause"
    return None


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    scan_dir = repo_root / "data" / "scan_results"
    validation_dir = repo_root / "data" / "validation"
    output_path = validation_dir / "latest_openclaw_report.json"
    run_jsonl_path = validation_dir / "paper_live_runs.jsonl"

    latest_scan_path, latest_scan = _load_latest_scan(scan_dir)
    latest_run = _load_last_jsonl_row(run_jsonl_path)

    runtime_metadata: dict[str, Any] = {}
    summary: dict[str, Any] = {}
    scan_run_id: str | None = None
    scan_generated_at: str | None = None

    if isinstance(latest_scan, dict):
        runtime_metadata = latest_scan.get("runtime_metadata", {}) or {}
        summary = latest_scan.get("summary", {}) or {}
        scan_run_id = latest_scan.get("run_id")
        scan_generated_at = latest_scan.get("generated_at")

    matched_run = _find_run_row_by_run_id(run_jsonl_path, scan_run_id)

    report: dict[str, Any] = {
        "report_generated_from": "options_algo_v2",
        "latest_scan_file": None if latest_scan_path is None else str(latest_scan_path),
        "latest_run_row_found": latest_run is not None,
        "paper_live_run_id_match_found": matched_run is not None,
        "paper_live_run_id_mismatch": False,
        "paper_live_latest_run_id": None,
        "paper_live_latest_timestamp_utc": None,
        "run_id": scan_run_id,
        "timestamp_utc": scan_generated_at,
        "as_of_date": runtime_metadata.get("as_of_date"),
        "runtime_mode": runtime_metadata.get("runtime_mode"),
        "strict_live_mode": runtime_metadata.get("strict_live_mode"),
        "symbol_count": summary.get("total_candidates"),
        "passed_count": summary.get("total_passed"),
        "rejected_count": summary.get("total_rejected"),
        "top_trade_candidate_symbols": runtime_metadata.get("top_trade_candidate_symbols", []),
        "trade_idea_symbols": runtime_metadata.get("trade_idea_symbols", []),
        "degraded_live_mode": runtime_metadata.get("degraded_live_mode"),
        "primary_degradation_cause": None,
        "top_rejection_reasons": summary.get("rejection_reason_counts", {}),
        "iv_rank_ready_symbols": [],
        "iv_rank_insufficient_history_symbols": [],
        "options_context_matched_count": runtime_metadata.get("options_context_matched_count"),
        "options_context_missing_count": runtime_metadata.get("options_context_missing_count"),
        "options_context_missing_symbols": runtime_metadata.get("options_context_missing_symbols", []),
        "options_context_regime_counts": runtime_metadata.get("options_context_regime_counts", {}),
        "options_context_low_confidence_symbols": runtime_metadata.get(
            "options_context_low_confidence_symbols",
            [],
        ),
        "options_context_top_expected_move_symbols": runtime_metadata.get(
            "options_context_top_expected_move_symbols",
            [],
        ),
        "options_context_top_skew_symbols": runtime_metadata.get(
            "options_context_top_skew_symbols",
            [],
        ),
        "options_context_decision_adjusted_symbol_count": runtime_metadata.get(
            "options_context_decision_adjusted_symbol_count"
        ),
        "options_context_hard_reject_count": runtime_metadata.get(
            "options_context_hard_reject_count"
        ),
        "options_context_applied_reason_counts": runtime_metadata.get(
            "options_context_applied_reason_counts",
            {},
        ),
    }

    if runtime_metadata:
        report["primary_degradation_cause"] = _primary_degradation_cause(runtime_metadata)
        report["iv_rank_ready_symbols"] = runtime_metadata.get("iv_rank_ready_symbols", [])
        report["iv_rank_insufficient_history_symbols"] = runtime_metadata.get(
            "iv_rank_insufficient_history_symbols",
            [],
        )

    if isinstance(latest_run, dict):
        report["paper_live_latest_run_id"] = latest_run.get("run_id")
        report["paper_live_latest_timestamp_utc"] = latest_run.get("timestamp_utc")
        if scan_run_id and latest_run.get("run_id") != scan_run_id:
            report["paper_live_run_id_mismatch"] = True

    if isinstance(matched_run, dict):
        report["timestamp_utc"] = matched_run.get("timestamp_utc") or report["timestamp_utc"]
        report["as_of_date"] = matched_run.get("as_of_date") or report["as_of_date"]
        report["runtime_mode"] = matched_run.get("runtime_mode") or report["runtime_mode"]
        report["strict_live_mode"] = matched_run.get("strict_live_mode")
        report["degraded_live_mode"] = matched_run.get("degraded_live_mode")
        report["top_trade_candidate_symbols"] = matched_run.get(
            "top_trade_candidate_symbols",
            report["top_trade_candidate_symbols"],
        )
        report["trade_idea_symbols"] = matched_run.get(
            "trade_idea_symbols",
            report["trade_idea_symbols"],
        )

    validation_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    print(output_path)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
