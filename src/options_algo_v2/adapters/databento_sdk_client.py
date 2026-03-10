from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatabentoHistoricalClientWrapper:
    api_key: str

    def get_underlying_snapshot(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> dict[str, object]:
        raise NotImplementedError("Databento SDK wrapper is not implemented")
