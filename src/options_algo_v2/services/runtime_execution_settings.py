from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, date, datetime


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean-like value")


def _get_as_of_date() -> date:
    raw = os.getenv("OPTIONS_ALGO_AS_OF_DATE")
    if raw is None or not raw.strip():
        return datetime.now(UTC).date()
    return date.fromisoformat(raw.strip())


@dataclass(frozen=True)
class RuntimeExecutionSettings:
    as_of_date: date
    strict_live_mode: bool
    allow_mock_historical_fallback: bool
    allow_breadth_override: bool
    allow_short_dte_fallback: bool
    allow_relaxed_liquidity_thresholds: bool


def get_runtime_execution_settings() -> RuntimeExecutionSettings:
    strict_live_mode = _get_bool("OPTIONS_ALGO_STRICT_LIVE_MODE", False)

    default_allow_fallbacks = not strict_live_mode

    return RuntimeExecutionSettings(
        as_of_date=_get_as_of_date(),
        strict_live_mode=strict_live_mode,
        allow_mock_historical_fallback=_get_bool(
            "OPTIONS_ALGO_ALLOW_MOCK_HISTORICAL_FALLBACK",
            default_allow_fallbacks,
        ),
        allow_breadth_override=_get_bool(
            "OPTIONS_ALGO_ALLOW_BREADTH_OVERRIDE",
            default_allow_fallbacks,
        ),
        allow_short_dte_fallback=_get_bool(
            "OPTIONS_ALGO_ALLOW_SHORT_DTE_FALLBACK",
            default_allow_fallbacks,
        ),
        allow_relaxed_liquidity_thresholds=_get_bool(
            "OPTIONS_ALGO_ALLOW_RELAXED_LIQUIDITY_THRESHOLDS",
            default_allow_fallbacks,
        ),
    )
