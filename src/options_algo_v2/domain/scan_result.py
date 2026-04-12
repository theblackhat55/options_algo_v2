from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScanSummary:
    total_candidates: int
    total_passed: int
    total_rejected: int
    passed_symbols: list[str] = field(default_factory=list)
    rejected_symbols: list[str] = field(default_factory=list)
    rejection_reason_counts: dict[str, int] = field(default_factory=dict)
    signal_state_counts: dict[str, int] = field(default_factory=dict)
    strategy_type_counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ScanResult:
    run_id: str
    generated_at: str
    config_versions: dict[str, str]
    summary: ScanSummary
    end_date: str | None = None
    as_of_date: str | None = None
    historical_row_provider: str | None = None
    options_provider: str | None = None
    run_quality: str | None = None
    is_test_run: bool = False
    trade_validation_version: str | None = None
    runtime_metadata: dict[str, object] = field(default_factory=dict)
    feature_sources: list[dict[str, str]] = field(default_factory=list)
    trade_candidates: list[dict[str, object]] = field(default_factory=list)
    trade_ideas: list[dict[str, object]] = field(default_factory=list)
    decisions: list[dict[str, object]] = field(default_factory=list)
