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
    runtime_metadata: dict[str, object] = field(default_factory=dict)
    decisions: list[dict[str, object]] = field(default_factory=list)
