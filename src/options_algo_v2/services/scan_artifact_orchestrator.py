from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.scan_result import ScanResult
from options_algo_v2.services.run_id import generate_run_id
from options_algo_v2.services.scan_result_builder import build_scan_result
from options_algo_v2.services.scan_result_writer import write_scan_result


@dataclass(frozen=True)
class ScanArtifactResult:
    scan_result: ScanResult
    output_path: Path


def build_and_write_scan_artifact(
    *,
    decisions: list[CandidateDecision],
    base_dir: str | Path = "data/scan_results",
    run_id: str | None = None,
    degraded_metadata: dict[str, object] | None = None,
    end_date: str | None = None,
) -> ScanArtifactResult:
    resolved_run_id = run_id or generate_run_id()

    scan_result = build_scan_result(
        run_id=resolved_run_id,
        decisions=decisions,
        degraded_metadata=degraded_metadata or {},
        end_date=end_date,
    )

    output_path = write_scan_result(
        scan_result=scan_result,
        base_dir=base_dir,
    )

    return ScanArtifactResult(
        scan_result=scan_result,
        output_path=output_path,
    )
