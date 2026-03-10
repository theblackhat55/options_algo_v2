from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.domain.bar_data import BarData
from options_algo_v2.domain.live_historical_row_client import LiveHistoricalRowClient


@dataclass(frozen=True)
class PlaceholderLiveHistoricalRowClient(LiveHistoricalRowClient):
    source: str = "live_historical_placeholder"

    def get_daily_bars(
        self,
        *,
        symbol: str,
        lookback_days: int,
        dataset: str,
        schema: str,
    ) -> list[BarData]:
        _ = symbol
        _ = lookback_days
        _ = dataset
        _ = schema
        raise NotImplementedError("live historical row client is not implemented")
