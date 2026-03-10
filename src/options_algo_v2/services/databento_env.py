from __future__ import annotations

import os


def get_databento_api_key() -> str:
    api_key = os.getenv("DATABENTO_API_KEY", "").strip()

    if not api_key:
        raise ValueError("DATABENTO_API_KEY is required for live runtime mode")

    return api_key
