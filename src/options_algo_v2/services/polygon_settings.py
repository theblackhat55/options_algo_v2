from __future__ import annotations

import os
from dataclasses import dataclass


def get_polygon_api_key() -> str:
    value = os.getenv("POLYGON_API_KEY", "").strip()
    if not value:
        raise ValueError("POLYGON_API_KEY is required for live options chain access")
    return value


def has_polygon_api_key() -> bool:
    return bool(os.getenv("POLYGON_API_KEY", "").strip())


def get_polygon_base_url() -> str:
    return os.getenv("POLYGON_BASE_URL", "https://api.polygon.io").rstrip("/")


def get_polygon_timeout_seconds() -> float:
    raw = os.getenv("POLYGON_TIMEOUT_SECONDS", "10")
    return float(raw)


@dataclass(frozen=True)
class PolygonSettings:
    api_key: str
    base_url: str = "https://api.polygon.io"
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> PolygonSettings:
        return cls(
            api_key=get_polygon_api_key(),
            base_url=get_polygon_base_url(),
            timeout_seconds=get_polygon_timeout_seconds(),
        )
