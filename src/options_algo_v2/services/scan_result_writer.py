from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from options_algo_v2.domain.scan_result import ScanResult


def build_scan_result_path(
    *,
    run_id: str,
    base_dir: str | Path = "data/scan_results",
) -> Path:
    output_dir = Path(base_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{run_id}.json"


def write_scan_result(
    *,
    scan_result: ScanResult,
    base_dir: str | Path = "data/scan_results",
) -> Path:
    output_path = build_scan_result_path(
        run_id=scan_result.run_id,
        base_dir=base_dir,
    )

    payload = asdict(scan_result)

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)

    return output_path
