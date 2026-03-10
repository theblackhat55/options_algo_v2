from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PolygonSettings:
    api_key: str
    base_url: str


def load_polygon_settings() -> PolygonSettings:
    api_key = os.getenv("POLYGON_API_KEY", "").strip()
    if not api_key:
        raise ValueError("POLYGON_API_KEY is required for live options chain mode")

    base_url = os.getenv("POLYGON_BASE_URL", "https://api.polygon.io").strip()
    if not base_url:
        raise ValueError("POLYGON_BASE_URL cannot be blank")

    return PolygonSettings(
        api_key=api_key,
        base_url=base_url,
    )
