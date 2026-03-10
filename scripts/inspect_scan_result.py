from __future__ import annotations

import json
import sys
from pathlib import Path


def inspect_scan_result(path_str: str) -> int:
    path = Path(path_str)

    if not path.exists():
        print(f"error=file_not_found path={path}")
        return 1

    payload = json.loads(path.read_text())

    summary = payload.get("summary", {})
    config_versions = payload.get("config_versions", {})
    runtime_metadata = payload.get("runtime_metadata", {})

    print(f"run_id={payload.get('run_id', '')}")
    print(f"generated_at={payload.get('generated_at', '')}")
    print(f"config_versions={config_versions}")
    print(f"runtime_mode={runtime_metadata.get('runtime_mode', '')}")
    print(f"databento_runtime={runtime_metadata.get('databento', {})}")
    print(
        "summary="
        f"total={summary.get('total_candidates', 0)},"
        f"passed={summary.get('total_passed', 0)},"
        f"rejected={summary.get('total_rejected', 0)}"
    )
    print(
        "rejection_reason_counts="
        f"{summary.get('rejection_reason_counts', {})}"
    )
    print(f"signal_state_counts={summary.get('signal_state_counts', {})}")
    print(f"strategy_type_counts={summary.get('strategy_type_counts', {})}")
    print(f"passed_symbols={summary.get('passed_symbols', [])}")
    print(f"rejected_symbols={summary.get('rejected_symbols', [])}")

    return 0


def main() -> None:
    if len(sys.argv) != 2:
        print("usage=python scripts/inspect_scan_result.py <scan_result.json>")
        raise SystemExit(1)

    raise SystemExit(inspect_scan_result(sys.argv[1]))


if __name__ == "__main__":
    main()
