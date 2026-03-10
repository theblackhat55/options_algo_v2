from __future__ import annotations

import os

from options_algo_v2.services.databento_settings import load_databento_settings


def build_databento_runtime_info() -> dict[str, str]:
    has_api_key = bool(os.getenv("DATABENTO_API_KEY", "").strip())

    if has_api_key:
        settings = load_databento_settings()
        dataset = settings.dataset
        schema = settings.schema
    else:
        dataset = os.getenv("DATABENTO_DATASET", "XNAS.ITCH").strip() or "XNAS.ITCH"
        schema = os.getenv("DATABENTO_SCHEMA", "ohlcv-1d").strip() or "ohlcv-1d"

    return {
        "dataset": dataset,
        "schema": schema,
        "has_api_key": "true" if has_api_key else "false",
    }
