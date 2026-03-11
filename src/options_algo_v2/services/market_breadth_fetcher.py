from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen


def fetch_live_market_breadth_payload() -> dict[str, object]:
    url = os.getenv("OPTIONS_ALGO_MARKET_BREADTH_URL", "").strip()
    static_pct = os.getenv(
        "OPTIONS_ALGO_MARKET_BREADTH_STATIC_PCT_ABOVE_20DMA",
        "",
    ).strip()
    static_timestamp = os.getenv(
        "OPTIONS_ALGO_MARKET_BREADTH_STATIC_TIMESTAMP",
        "",
    ).strip()

    if static_pct:
        timestamp = static_timestamp or "1970-01-01T00:00:00Z"
        return {
            "pct_above_20dma": static_pct,
            "timestamp": timestamp,
        }

    if not url:
        raise RuntimeError("live market breadth data source is not configured")

    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "options-algo-v2/1.0",
        },
    )
    with urlopen(request, timeout=10.0) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))

    if not isinstance(payload, dict):
        raise RuntimeError("market breadth payload must be a JSON object")

    return payload
