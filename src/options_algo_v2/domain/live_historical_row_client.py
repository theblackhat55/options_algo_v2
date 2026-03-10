from __future__ import annotations

from typing import Protocol

from options_algo_v2.domain.bar_data import BarData


class LiveHistoricalRowClient(Protocol):
    def get_daily_bars(
        self,
        *,
        symbol: str,
        lookback_days: int,
        dataset: str,
        schema: str,
    ) -> list[BarData]: ...
