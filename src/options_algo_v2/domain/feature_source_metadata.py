from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureSourceMetadata:
    symbol: str
    historical_row_provider: str
    market_breadth_provider: str
    dataset: str
    schema: str
