from __future__ import annotations

from datetime import UTC, datetime


def generate_run_id(prefix: str = "scan") -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{timestamp}"
