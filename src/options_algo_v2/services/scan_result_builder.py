from __future__ import annotations

from datetime import UTC, datetime

from options_algo_v2.config.rulebook_config import load_rulebook_configs
from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.scan_result import ScanResult, ScanSummary
from options_algo_v2.services.contract_selection_diagnostics import (
    count_trade_candidates_by_expiration,
)
from options_algo_v2.services.databento_runtime_info import (
    build_databento_runtime_info,
)
from options_algo_v2.services.decision_diagnostics import (
    borderline_score_failure_summary,
    count_blocking_reasons,
    count_directional_blockers,
    count_directional_states,
    count_failure_archetypes,
    count_non_actionable_directional_states,
    count_rejection_reasons,
    count_score_gap_buckets,
    count_signal_states,
    count_soft_penalty_reasons,
    count_strategy_types,
    directional_failure_summary,
    failure_archetype_by_symbol,
    failure_archetype_review_slices,
    highest_score_failed_decisions,
    highest_score_failing_decision,
    list_near_threshold_failures,
    list_non_actionable_directional_symbols,
    list_passed_with_soft_penalties_symbols,
    lowest_score_passing_decision,
    near_threshold_failure_decisions,
    passed_with_soft_penalties_decisions,
    score_plus_soft_penalty_summary,
    top_passed_decisions,
)
from options_algo_v2.services.decision_serializer import serialize_candidate_decision
from options_algo_v2.services.feature_source_diagnostics import (
    count_feature_sources_by_dataset_schema,
    count_feature_sources_by_historical_row_provider,
    count_feature_sources_by_market_breadth_provider,
)
from options_algo_v2.services.feature_source_metadata_builder import (
    build_feature_source_metadata,
)
from options_algo_v2.services.historical_row_provider_factory import (
    get_historical_row_provider_name,
    get_historical_row_provider_source,
)
from options_algo_v2.services.market_breadth_provider_factory import (
    get_market_breadth_provider_name,
    get_market_breadth_provider_source,
)
from options_algo_v2.services.options_chain_provider_factory import (
    get_options_chain_provider_name,
    get_options_chain_provider_source,
)
from options_algo_v2.services.runtime_execution_settings import (
    get_runtime_execution_settings,
)
from options_algo_v2.services.runtime_mode import get_runtime_mode
from options_algo_v2.services.scan_trade_candidate_builder import (
    build_serialized_trade_candidates,
)
from options_algo_v2.services.serialized_trade_candidate_selector import (
    rank_serialized_trade_candidates,
)
from options_algo_v2.services.top_trade_summary_builder import (
    build_top_trade_summary_rows,
)
from options_algo_v2.services.trade_candidate_diagnostics import (
    count_trade_candidates_by_strategy_family,
    count_trade_candidates_by_symbol,
)
from options_algo_v2.services.trade_candidate_ranking import (
    rank_trade_candidates,
    select_top_trade_candidates,
)
from options_algo_v2.services.trade_candidate_selection_diagnostics import (
    count_ranked_trade_candidates_by_strategy_family,
    list_ranked_trade_candidate_symbols,
)
from options_algo_v2.services.trade_idea_builder import (
    build_trade_ideas,
)
from options_algo_v2.services.trade_idea_diagnostics import (
    count_trade_ideas_by_strategy_family,
    list_trade_idea_symbols,
)


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value).strip()
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def _validate_trade_idea(trade_idea: dict[str, object]) -> tuple[bool, list[str]]:
    errors: list[str] = []

    strategy_type = str(trade_idea.get("strategy_type", "") or "").strip()
    symbol = str(trade_idea.get("symbol", "") or "").strip()
    expiration = str(
        trade_idea.get("expiration", "") or trade_idea.get("expiry", "") or ""
    ).strip()

    if not strategy_type:
        errors.append("missing_strategy_type")
    if not symbol:
        errors.append("missing_symbol")
    if not expiration:
        errors.append("missing_expiration")

    short_strike = _to_float(trade_idea.get("short_strike"))
    long_strike = _to_float(trade_idea.get("long_strike"))
    width = _to_float(trade_idea.get("width"))
    max_risk = _to_float(trade_idea.get("max_risk"))
    net_credit = _to_float(trade_idea.get("net_credit"))

    if short_strike is not None and long_strike is not None and width is not None:
        if abs(abs(short_strike - long_strike) - width) > 0.01:
            errors.append("width_mismatch")

    if width is not None and width <= 0:
        errors.append("nonpositive_width")

    if max_risk is not None and max_risk < 0:
        errors.append("negative_max_risk")

    if max_risk is not None and width is not None and width > 0 and max_risk == 0:
        errors.append("zero_risk_defined_spread")

    if net_credit is not None and width is not None and net_credit - width > 0.01:
        errors.append("credit_exceeds_width")

    return (len(errors) == 0, errors)


TRADE_VALIDATION_VERSION = "trade_validation_v1"


def _attach_trade_validation_metadata(
    trade_ideas: list[dict[str, object]],
) -> list[dict[str, object]]:
    enriched: list[dict[str, object]] = []

    for trade_idea in trade_ideas:
        item = dict(trade_idea)
        is_valid, errors = _validate_trade_idea(item)
        item["is_structurally_valid_trade"] = is_valid
        item["trade_validation_errors"] = errors
        item["trade_validation_version"] = TRADE_VALIDATION_VERSION
        enriched.append(item)

    return enriched


def _feature_sources_by_symbol(
    feature_sources: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    by_symbol: dict[str, dict[str, str]] = {}
    for item in feature_sources:
        symbol = item.get("symbol")
        if isinstance(symbol, str) and symbol:
            by_symbol[symbol] = dict(item)
    return by_symbol


def _build_feature_debug_by_symbol(
    feature_sources: list[dict[str, str]],
) -> dict[str, dict[str, object]]:
    by_symbol = _feature_sources_by_symbol(feature_sources)

    result: dict[str, dict[str, object]] = {}
    for symbol, source in by_symbol.items():
        result[symbol] = {
            "symbol": symbol,
            "dataset": source.get("dataset"),
            "schema": source.get("schema"),
            "historical_row_provider": source.get("historical_row_provider"),
            "market_breadth_provider": source.get("market_breadth_provider"),
        }
    return result


def _build_decision_trace_by_symbol(
    serialized_decisions: list[dict[str, object]],
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}

    for item in serialized_decisions:
        symbol = item.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            continue

        rejection_reasons = item.get("rejection_reasons")
        if isinstance(rejection_reasons, list):
            reasons = [str(x) for x in rejection_reasons]
        else:
            reasons = []

        result[symbol] = {
            "symbol": symbol,
            "directional_state": item.get("directional_state"),
            "market_regime": item.get("market_regime"),
            "iv_state": item.get("iv_state"),
            "signal_state": item.get("signal_state"),
            "strategy_type": item.get("strategy_type"),
            "strategy_family": item.get("strategy_type"),
            "final_passed": item.get("final_passed"),
            "final_score": item.get("final_score"),
            "min_score_required": item.get("min_score_required"),
            "rationale": item.get("rationale"),
            "rejection_reasons": reasons,
            "event_filter": item.get("event_filter"),
            "extension_filter": item.get("extension_filter"),
            "liquidity_filter": item.get("liquidity_filter"),
        }

    return result


def _enrich_trade_candidates_with_options_context(
    trade_candidates: list[dict[str, object]],
    options_context_by_symbol: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    enriched: list[dict[str, object]] = []

    for candidate in trade_candidates:
        row = dict(candidate)
        symbol = row.get("symbol")
        context = (
            options_context_by_symbol.get(str(symbol), {})
            if isinstance(symbol, str)
            else {}
        )

        row["options_context_available"] = context.get("context_available")
        row["options_context_confidence_score"] = context.get("confidence_score")
        row["options_context_regime"] = context.get("options_summary_regime")
        row["options_context_expected_move_1d_pct"] = context.get("expected_move_1d_pct")
        row["options_context_expected_move_1w_pct"] = context.get("expected_move_1w_pct")
        row["options_context_expected_move_30d_pct"] = context.get("expected_move_30d_pct")
        row["options_context_skew_25d_put_call_ratio"] = context.get(
            "skew_25d_put_call_ratio"
        )
        row["options_context_skew_25d_put_call_spread"] = context.get(
            "skew_25d_put_call_spread"
        )
        row["options_context_pcr_oi"] = context.get("pcr_oi")
        row["options_context_pcr_volume"] = context.get("pcr_volume")
        enriched.append(row)

    return enriched


def _summarize_options_context_decision_debug(
    debug_by_symbol: dict[str, dict[str, object]],
) -> dict[str, object]:
    adjusted_symbol_count = 0
    hard_reject_count = 0
    reason_counts: dict[str, int] = {}

    for item in debug_by_symbol.values():
        if not isinstance(item, dict):
            continue
        adjusted_symbol_count += 1
        if item.get("hard_reject"):
            hard_reject_count += 1

        reasons = item.get("applied_reason_codes", [])
        if isinstance(reasons, list):
            for reason in reasons:
                key = str(reason)
                reason_counts[key] = reason_counts.get(key, 0) + 1

    return {
        "options_context_decision_adjusted_symbol_count": adjusted_symbol_count,
        "options_context_hard_reject_count": hard_reject_count,
        "options_context_applied_reason_counts": reason_counts,
    }


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
    degraded_metadata: dict[str, object] | None = None,
    end_date: str | None = None,
) -> ScanResult:
    configs = load_rulebook_configs()
    execution_settings = get_runtime_execution_settings()

    config_versions = {
        "universe": str(configs.universe.get("version", "unknown")),
        "strategy": str(configs.strategy.get("version", "unknown")),
        "risk": str(configs.risk.get("version", "unknown")),
    }

    generated_at = datetime.now(UTC).isoformat()
    summary = build_scan_summary(decisions)
    serialized_decisions = [
        serialize_candidate_decision(decision) for decision in decisions
    ]
    feature_sources = [
        {
            "symbol": metadata.symbol,
            "historical_row_provider": metadata.historical_row_provider,
            "market_breadth_provider": metadata.market_breadth_provider,
            "dataset": metadata.dataset,
            "schema": metadata.schema,
        }
        for metadata in (
            build_feature_source_metadata(symbol=decision.candidate.symbol)
            for decision in decisions
        )
    ]
    runtime_mode = get_runtime_mode()
    trade_candidates = build_serialized_trade_candidates(
        decisions=decisions,
        expiration="2026-04-17",
        min_open_interest=0
        if execution_settings.allow_relaxed_liquidity_thresholds and runtime_mode == "live"
        else 900,
        max_bid_ask_spread_width=5.0
        if execution_settings.allow_relaxed_liquidity_thresholds and runtime_mode == "live"
        else 0.5,
        as_of_date=execution_settings.as_of_date,
    )

    degraded_metadata = degraded_metadata or {}
    options_context_by_symbol = degraded_metadata.get("options_context_by_symbol", {})
    if isinstance(options_context_by_symbol, dict):
        trade_candidates = _enrich_trade_candidates_with_options_context(
            trade_candidates,
            options_context_by_symbol,
        )
    ranked_trade_candidates = rank_trade_candidates(trade_candidates)
    top_trade_candidates = select_top_trade_candidates(
        ranked_trade_candidates,
        top_n=3,
    )
    ranked_selected_trade_candidates = rank_serialized_trade_candidates(
        trade_candidates
    )
    top_trade_summary_rows = build_top_trade_summary_rows(top_trade_candidates)
    trade_ideas = _attach_trade_validation_metadata(
        [
            dict(item)
            for item in build_trade_ideas(
                trade_candidates=trade_candidates,
                decisions=serialized_decisions,
            )
        ]
    )

    options_context_decision_debug_by_symbol = degraded_metadata.get(
        "options_context_decision_debug_by_symbol",
        {},
    ) if degraded_metadata else {}

    options_context_decision_summary = (
        _summarize_options_context_decision_debug(options_context_decision_debug_by_symbol)
        if isinstance(options_context_decision_debug_by_symbol, dict)
        else {}
    )

    passed_with_soft_penalties_symbols = list_passed_with_soft_penalties_symbols(
        serialized_decisions
    )
    near_threshold_failures = list_near_threshold_failures(serialized_decisions)

    runtime_metadata: dict[str, object] = {
        "feature_debug_by_symbol": _build_feature_debug_by_symbol(feature_sources),
        "decision_trace_by_symbol": _build_decision_trace_by_symbol(serialized_decisions),
        "runtime_mode": get_runtime_mode(),
        "run_quality": (
            "mock"
            if get_historical_row_provider_name() == "mock"
            else "live"
            if get_historical_row_provider_name() in {"databento", "sqlite", "sqlite-first"}
            else "unknown"
        ),
        "is_mock": get_historical_row_provider_name() == "mock",
        "is_degraded": bool(
            degraded_metadata.get("degraded_live_mode")
            or degraded_metadata.get("used_mock_historical_fallback")
            or degraded_metadata.get("used_breadth_override")
            or degraded_metadata.get("used_placeholder_iv_inputs")
            or degraded_metadata.get("used_placeholder_liquidity_inputs")
        ),
        "is_reviewable": get_historical_row_provider_name() in {"databento", "sqlite", "sqlite-first"},
        "databento": build_databento_runtime_info(),
        "historical_row_provider": get_historical_row_provider_name(),
        "historical_row_provider_source": get_historical_row_provider_source(),
        "market_breadth_provider": get_market_breadth_provider_name(),
        "market_breadth_provider_source": get_market_breadth_provider_source(),
        "options_chain_provider": get_options_chain_provider_name(),
        "options_chain_provider_source": get_options_chain_provider_source(),
        "feature_source_counts_by_historical_row_provider": (
            count_feature_sources_by_historical_row_provider(feature_sources)
        ),
        "feature_source_counts_by_market_breadth_provider": (
            count_feature_sources_by_market_breadth_provider(feature_sources)
        ),
        "feature_source_counts_by_dataset_schema": (
            count_feature_sources_by_dataset_schema(feature_sources)
        ),
        "trade_candidate_counts_by_strategy_family": (
            count_trade_candidates_by_strategy_family(trade_candidates)
        ),
        "trade_candidate_counts_by_symbol": (
            count_trade_candidates_by_symbol(trade_candidates)
        ),
        "trade_candidate_counts_by_expiration": (
            count_trade_candidates_by_expiration(trade_candidates)
        ),
        "selected_trade_candidate_expirations": sorted(
            {
                str(item.get("expiration", "unknown"))
                for item in trade_candidates
            }
        ),
        "selected_trade_candidate_symbols": [
            str(item.get("symbol", "unknown")) for item in trade_candidates
        ],
        "selected_trade_candidate_count": len(trade_candidates),
        "ranked_trade_candidate_counts_by_strategy_family": (
            count_ranked_trade_candidates_by_strategy_family(
                ranked_selected_trade_candidates
            )
        ),
        "ranked_trade_candidate_symbols": list_ranked_trade_candidate_symbols(
            ranked_selected_trade_candidates
        ),
        "top_trade_candidate_symbols": [
            str(item.get("symbol", "unknown")) for item in top_trade_candidates
        ],
        "trade_idea_count": len(trade_ideas),
        "trade_idea_symbols": list_trade_idea_symbols(trade_ideas),
        "trade_idea_counts_by_strategy_family": (
            count_trade_ideas_by_strategy_family(trade_ideas)
        ),
        "directional_state_counts": count_directional_states(decisions),
        "non_actionable_directional_state_counts": (
            count_non_actionable_directional_states(decisions)
        ),
        "non_actionable_directional_state_count": sum(
            count_non_actionable_directional_states(decisions).values()
        ),
        "non_actionable_directional_symbols": (
            list_non_actionable_directional_symbols(decisions)
        ),
        "directional_blocker_counts": count_directional_blockers(serialized_decisions),
        "blocking_reason_counts": count_blocking_reasons(serialized_decisions),
        "soft_penalty_reason_counts": count_soft_penalty_reasons(serialized_decisions),
        "failure_archetype_counts": count_failure_archetypes(serialized_decisions),
        "failure_archetype_by_symbol": failure_archetype_by_symbol(serialized_decisions),
        "failure_archetype_review_slices": failure_archetype_review_slices(
            serialized_decisions
        ),
        "directional_failure_summary": directional_failure_summary(serialized_decisions),
        "score_plus_soft_penalty_summary": score_plus_soft_penalty_summary(
            serialized_decisions
        ),
        "borderline_score_failure_summary": borderline_score_failure_summary(
            serialized_decisions
        ),
        "passed_with_soft_penalties_symbols": passed_with_soft_penalties_symbols,
        "passed_with_soft_penalties_count": len(passed_with_soft_penalties_symbols),
        "near_threshold_failures": near_threshold_failures,
        "near_threshold_failure_symbols": [
            str(item.get("symbol", "unknown")) for item in near_threshold_failures
        ],
        "near_threshold_failure_count": len(near_threshold_failures),
        "score_gap_bucket_counts": count_score_gap_buckets(serialized_decisions),
        "highest_score_failing_decision": highest_score_failing_decision(serialized_decisions),
        "lowest_score_passing_decision": lowest_score_passing_decision(serialized_decisions),
        "top_passed_decisions": top_passed_decisions(serialized_decisions),
        "highest_score_failed_decisions": highest_score_failed_decisions(serialized_decisions),
        "passed_with_soft_penalties_decisions": passed_with_soft_penalties_decisions(
            serialized_decisions
        ),
        "near_threshold_failure_decisions": near_threshold_failure_decisions(
            serialized_decisions
        ),
        "top_trade_summary_rows": top_trade_summary_rows,
    }

    runtime_metadata.update(options_context_decision_summary)

    if degraded_metadata:
        runtime_metadata.update(degraded_metadata)

    return ScanResult(
        run_id=run_id,
        generated_at=generated_at,
        config_versions=config_versions,
        summary=summary,
        end_date=end_date,
        as_of_date=execution_settings.as_of_date.isoformat(),
        historical_row_provider=get_historical_row_provider_name(),
        options_provider=get_options_chain_provider_name(),
        run_quality=runtime_metadata.get("run_quality"),
        is_test_run=runtime_mode != "live",
        trade_validation_version=TRADE_VALIDATION_VERSION,
        runtime_metadata=runtime_metadata,
        feature_sources=feature_sources,
        trade_candidates=ranked_trade_candidates,
        trade_ideas=trade_ideas,
        decisions=serialized_decisions,
    )
