from __future__ import annotations

from datetime import UTC, datetime

from options_algo_v2.config.rulebook_config import load_rulebook_configs
from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.scan_result import ScanResult, ScanSummary
from options_algo_v2.services.databento_runtime_info import (
    build_databento_runtime_info,
)
from options_algo_v2.services.decision_diagnostics import (
    count_rejection_reasons,
    count_signal_states,
    count_strategy_types,
)
from options_algo_v2.services.decision_serializer import serialize_candidate_decision
from options_algo_v2.services.historical_row_provider_factory import (
    get_historical_row_provider_name,
)
from options_algo_v2.services.market_breadth_provider_factory import (
    get_market_breadth_provider_name,
)
from options_algo_v2.services.runtime_mode import get_runtime_mode


def build_scan_summary(decisions: list[CandidateDecision]) -> ScanSummary:
    passed_symbols = [d.candidate.symbol for d in decisions if d.final_passed]
    rejected_symbols = [d.candidate.symbol for d in decisions if not d.final_passed]

    return ScanSummary(
        total_candidates=len(decisions),
        total_passed=len(passed_symbols),
        total_rejected=len(rejected_symbols),
        passed_symbols=passed_symbols,
        rejected_symbols=rejected_symbols,
        rejection_reason_counts=count_rejection_reasons(decisions),
        signal_state_counts=count_signal_states(decisions),
        strategy_type_counts=count_strategy_types(decisions),
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

    runtime_metadata: dict[str, object] = {
        "runtime_mode": get_runtime_mode(),
        "databento": build_databento_runtime_info(),
        "historical_row_provider": get_historical_row_provider_name(),
        "market_breadth_provider": get_market_breadth_provider_name(),
    }

    return ScanResult(
        run_id=run_id,
        generated_at=generated_at,
        config_versions=config_versions,
        summary=summary,
        runtime_metadata=runtime_metadata,
        decisions=serialized_decisions,
    )
