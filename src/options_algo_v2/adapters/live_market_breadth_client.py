from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from options_algo_v2.domain.market_breadth_snapshot import MarketBreadthSnapshot
from options_algo_v2.services.market_breadth_fetcher import (
    fetch_live_market_breadth_payload,
)

PayloadFetcher = Callable[[], dict[str, object]]


@dataclass(frozen=True)
class LiveMarketBreadthClient:
    fetch_payload: PayloadFetcher = fetch_live_market_breadth_payload
    source: str = "market_breadth_live"

    def get_market_breadth_snapshot(self) -> MarketBreadthSnapshot:
        payload = self.fetch_payload()
        return self.normalize_payload(payload)

    def normalize_payload(
        self,
        payload: dict[str, object],
    ) -> MarketBreadthSnapshot:
        pct = self._to_float(payload.get("pct_above_20dma"))
        timestamp = payload.get("timestamp")

        if pct is None:
            raise ValueError("pct_above_20dma is required")
        if timestamp is None:
            raise ValueError("timestamp is required")

        return MarketBreadthSnapshot(
            pct_above_20dma=pct,
            timestamp=str(timestamp),
            source=self.source,
        )

    @staticmethod
    def _to_float(value: object) -> float | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return float(stripped)
            except ValueError:
                return None
        return None


class PlaceholderLiveMarketBreadthClient(LiveMarketBreadthClient):
    """Backward-compatible alias for older imports/tests."""

    pass
