from __future__ import annotations

from datetime import UTC, datetime

from options_algo_v2.config.rulebook_config import load_rulebook_configs
from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.scan_result import ScanResult, ScanSummary
from options_algo_v2.services.decision_serializer import serialize_candidate_decision


def build_scan_summary(decisions: list[CandidateDecision]) -> ScanSummary:
    passed_symbols = [d.candidate.symbol for d in decisions if d.final_passed]
    rejected_symbols = [d.candidate.symbol for d in decisions if not d.final_passed]

    return ScanSummary(
        total_candidates=len(decisions),
        total_passed=len(passed_symbols),
        total_rejected=len(rejected_symbols),
        passed_symbols=passed_symbols,
        rejected_symbols=rejected_symbols,
    )


def build_scan_result(
    *,
    run_id: str,
    decisions: list[CandidateDecision],
) -> ScanResult:
    configs = load_rulebook_configs()

    config_versions = {
        "universe": str(configs.universe.get("version", "unknown")),
        "strategy": str(configs.strategy.get("version", "unknown")),
        "risk": str(configs.risk.get("version", "unknown")),
    }

    generated_at = datetime.now(UTC).isoformat()
    summary = build_scan_summary(decisions)
    serialized_decisions = [serialize_candidate_decision(decision) for decision in decisions]

    return ScanResult(
        run_id=run_id,
        generated_at=generated_at,
        config_versions=config_versions,
        summary=summary,
        decisions=serialized_decisions,
    )
