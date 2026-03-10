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

    print(f"run_id={payload.get('run_id', 'unknown')}")
    print(f"generated_at={payload.get('generated_at', 'unknown')}")
    print(f"config_versions={payload.get('config_versions', {})}")

    runtime_metadata = payload.get("runtime_metadata", {})
    print(f"runtime_mode={runtime_metadata.get('runtime_mode', 'unknown')}")
    print(
        "historical_row_provider="
        f"{runtime_metadata.get('historical_row_provider', 'unknown')}"
    )
    print(
        "historical_row_provider_source="
        f"{runtime_metadata.get('historical_row_provider_source', 'unknown')}"
    )
    print(
        "market_breadth_provider="
        f"{runtime_metadata.get('market_breadth_provider', 'unknown')}"
    )
    print(
        "market_breadth_provider_source="
        f"{runtime_metadata.get('market_breadth_provider_source', 'unknown')}"
    )
    print(
        "options_chain_provider="
        f"{runtime_metadata.get('options_chain_provider', 'unknown')}"
    )
    print(
        "options_chain_provider_source="
        f"{runtime_metadata.get('options_chain_provider_source', 'unknown')}"
    )
    print(f"databento_runtime={runtime_metadata.get('databento', {})}")
    print(
        "feature_source_counts_by_historical_row_provider="
        f"{runtime_metadata.get('feature_source_counts_by_historical_row_provider', {})}"
    )
    print(
        "feature_source_counts_by_market_breadth_provider="
        f"{runtime_metadata.get('feature_source_counts_by_market_breadth_provider', {})}"
    )
    print(
        "feature_source_counts_by_dataset_schema="
        f"{runtime_metadata.get('feature_source_counts_by_dataset_schema', {})}"
    )
    print(
        "trade_candidate_counts_by_strategy_family="
        f"{runtime_metadata.get('trade_candidate_counts_by_strategy_family', {})}"
    )
    print(
        "trade_candidate_counts_by_symbol="
        f"{runtime_metadata.get('trade_candidate_counts_by_symbol', {})}"
    )
    print(
        "ranked_trade_candidate_counts_by_strategy_family="
        f"{runtime_metadata.get('ranked_trade_candidate_counts_by_strategy_family', {})}"
    )
    print(
        "ranked_trade_candidate_symbols="
        f"{runtime_metadata.get('ranked_trade_candidate_symbols', [])}"
    )
    print(
        "trade_candidate_counts_by_expiration="
        f"{runtime_metadata.get('trade_candidate_counts_by_expiration', {})}"
    )
    print(
        "selected_trade_candidate_expirations="
        f"{runtime_metadata.get('selected_trade_candidate_expirations', [])}"
    )
    print(
        "selected_trade_candidate_symbols="
        f"{runtime_metadata.get('selected_trade_candidate_symbols', [])}"
    )
    print(
        "selected_trade_candidate_count="
        f"{runtime_metadata.get('selected_trade_candidate_count', 0)}"
    )
    print(
        "top_trade_candidate_symbols="
        f"{runtime_metadata.get('top_trade_candidate_symbols', [])}"
    )
    print(
        "trade_idea_count="
        f"{runtime_metadata.get('trade_idea_count', 0)}"
    )
    print(
        "trade_idea_symbols="
        f"{runtime_metadata.get('trade_idea_symbols', [])}"
    )
    print(
        "trade_idea_counts_by_strategy_family="
        f"{runtime_metadata.get('trade_idea_counts_by_strategy_family', {})}"
    )
    print(
        "top_trade_summary_rows="
        f"{runtime_metadata.get('top_trade_summary_rows', [])}"
    )

    feature_sources = payload.get("feature_sources", [])
    print(f"feature_sources={feature_sources}")

    trade_candidates = payload.get("trade_candidates", [])
    print(f"trade_candidates={trade_candidates}")

    trade_ideas = payload.get("trade_ideas", [])
    print(f"trade_ideas={trade_ideas}")

    summary = payload.get("summary", {})
    print(
        f"summary=total={summary.get('total_candidates', 0)},"
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage=PYTHONPATH=src python scripts/inspect_scan_result.py <artifact.json>")
        raise SystemExit(1)

    raise SystemExit(inspect_scan_result(sys.argv[1]))
