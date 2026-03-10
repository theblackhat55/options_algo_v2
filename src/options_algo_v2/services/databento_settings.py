from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabentoSettings:
    api_key: str
    dataset: str
    schema: str


def load_databento_settings() -> DatabentoSettings:
    api_key = os.getenv("DATABENTO_API_KEY", "").strip()
    dataset = os.getenv("DATABENTO_DATASET", "XNAS.ITCH").strip()
    schema = os.getenv("DATABENTO_SCHEMA", "ohlcv-1d").strip()

    if not api_key:
        raise ValueError("DATABENTO_API_KEY is required for live runtime mode")

    if not dataset:
        raise ValueError("DATABENTO_DATASET cannot be blank")

    if not schema:
        raise ValueError("DATABENTO_SCHEMA cannot be blank")

    return DatabentoSettings(
        api_key=api_key,
        dataset=dataset,
        schema=schema,
    )
