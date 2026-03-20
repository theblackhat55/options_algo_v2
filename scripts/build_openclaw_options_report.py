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


def _load_last_jsonl_row(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    last: dict[str, Any] | None = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            last = row
    return last


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

    latest_scan_path, latest_scan = _load_latest_scan(scan_dir)
    latest_run = _load_last_jsonl_row(validation_dir / "paper_live_runs.jsonl")

    runtime_metadata = {}
    summary = {}

    if isinstance(latest_scan, dict):
        runtime_metadata = latest_scan.get("runtime_metadata", {}) or {}
        summary = latest_scan.get("summary", {}) or {}

    report: dict[str, Any] = {
        "report_generated_from": "options_algo_v2",
        "latest_scan_file": None if latest_scan_path is None else str(latest_scan_path),
        "latest_run_row_found": latest_run is not None,
        "run_id": None,
        "timestamp_utc": None,
        "as_of_date": None,
        "runtime_mode": None,
        "strict_live_mode": None,
        "symbol_count": None,
        "passed_count": None,
        "rejected_count": None,
        "top_trade_candidate_symbols": [],
        "trade_idea_symbols": [],
        "degraded_live_mode": None,
        "primary_degradation_cause": None,
        "top_rejection_reasons": {},
        "iv_rank_ready_symbols": [],
        "iv_rank_insufficient_history_symbols": [],
    }

    if isinstance(latest_run, dict):
        report["run_id"] = latest_run.get("run_id")
        report["timestamp_utc"] = latest_run.get("timestamp_utc")
        report["as_of_date"] = latest_run.get("as_of_date")
        report["runtime_mode"] = latest_run.get("runtime_mode")
        report["strict_live_mode"] = latest_run.get("strict_live_mode")
        report["symbol_count"] = latest_run.get("symbol_count")
        report["passed_count"] = latest_run.get("passed_count")
        report["rejected_count"] = latest_run.get("rejected_count")
        report["top_trade_candidate_symbols"] = latest_run.get("top_trade_candidate_symbols", [])
        report["trade_idea_symbols"] = latest_run.get("trade_idea_symbols", [])
        report["degraded_live_mode"] = latest_run.get("degraded_live_mode")

    if runtime_metadata:
        report["primary_degradation_cause"] = _primary_degradation_cause(runtime_metadata)
        report["iv_rank_ready_symbols"] = runtime_metadata.get("iv_rank_ready_symbols", [])
        report["iv_rank_insufficient_history_symbols"] = runtime_metadata.get(
            "iv_rank_insufficient_history_symbols",
            [],
        )

    if summary:
        report["top_rejection_reasons"] = summary.get("rejection_reason_counts", {})

    validation_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    print(output_path)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
