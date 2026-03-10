from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QualificationResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)
