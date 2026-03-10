from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from options_algo_v2.services.databento_settings import DatabentoSettings


@dataclass(frozen=True)
class DatabentoLiveHistoricalRowClient:
    settings: DatabentoSettings
    fetch_rows: Callable[[str, int, str, str, str], list[dict[str, object]]]
    source: str = "databento"

    def get_daily_rows(
        self,
        *,
        symbol: str,
        lookback_days: int,
        dataset: str,
        schema: str,
    ) -> list[dict[str, object]]:
        raw_rows = self.fetch_rows(
            symbol,
            lookback_days,
            dataset,
            schema,
            self.settings.api_key,
        )
        return self.normalize_rows(raw_rows)

    def normalize_rows(
        self,
        raw_rows: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []

        for row in raw_rows:
            ts_event = row.get("ts_event") or row.get("timestamp")
            open_ = self._to_float(row.get("open"))
            high = self._to_float(row.get("high"))
            low = self._to_float(row.get("low"))
            close = self._to_float(row.get("close"))
            volume = self._to_int(row.get("volume"))

            if ts_event is None:
                continue
            if open_ is None or high is None or low is None or close is None:
                continue
            if volume is None:
                continue

            normalized.append(
                {
                    "ts_event": str(ts_event),
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )

        return normalized

    @staticmethod
    def _to_float(value: object) -> float | None:
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

    @staticmethod
    def _to_int(value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return int(float(stripped))
            except ValueError:
                return None
        return None
