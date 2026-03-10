from __future__ import annotations

import json
import sys
from pathlib import Path

from options_algo_v2.services.feature_source_diagnostics import (
    count_feature_sources_by_dataset_schema,
    count_feature_sources_by_historical_row_provider,
    count_feature_sources_by_market_breadth_provider,
)


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
        "market_breadth_provider="
        f"{runtime_metadata.get('market_breadth_provider', 'unknown')}"
    )
    print(
        "market_breadth_provider_source="
        f"{runtime_metadata.get('market_breadth_provider_source', 'unknown')}"
    )
    print(f"databento_runtime={runtime_metadata.get('databento', {})}")

    feature_sources = payload.get("feature_sources", [])
    print(f"feature_sources={feature_sources}")
    print(
        "feature_source_counts_by_historical_row_provider="
        f"{count_feature_sources_by_historical_row_provider(feature_sources)}"
    )
    print(
        "feature_source_counts_by_market_breadth_provider="
        f"{count_feature_sources_by_market_breadth_provider(feature_sources)}"
    )
    print(
        "feature_source_counts_by_dataset_schema="
        f"{count_feature_sources_by_dataset_schema(feature_sources)}"
    )

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
