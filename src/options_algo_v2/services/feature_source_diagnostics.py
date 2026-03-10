from __future__ import annotations


def count_feature_sources_by_historical_row_provider(
    feature_sources: list[dict[str, str]],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in feature_sources:
        key = item.get("historical_row_provider", "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def count_feature_sources_by_market_breadth_provider(
    feature_sources: list[dict[str, str]],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in feature_sources:
        key = item.get("market_breadth_provider", "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def count_feature_sources_by_dataset_schema(
    feature_sources: list[dict[str, str]],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in feature_sources:
        dataset = item.get("dataset", "unknown")
        schema = item.get("schema", "unknown")
        key = f"{dataset}|{schema}"
        counts[key] = counts.get(key, 0) + 1
    return counts
