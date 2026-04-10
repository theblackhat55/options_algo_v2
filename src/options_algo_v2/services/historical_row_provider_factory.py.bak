from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.adapters.databento_live_historical_row_client import (
    DatabentoLiveHistoricalRowClient,
)
from options_algo_v2.domain.historical_row_provider import HistoricalRowProvider
from options_algo_v2.services.databento_historical_fetcher import (
    fetch_databento_daily_rows,
)
from options_algo_v2.services.databento_settings import load_databento_settings
from options_algo_v2.services.mock_historical_rows import build_mock_historical_rows
from options_algo_v2.services.runtime_mode import get_runtime_mode


def _load_live_databento_settings():
    return load_databento_settings()


@dataclass(frozen=True)
class MockHistoricalRowProvider(HistoricalRowProvider):
    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
        end_date: str | None = None,
    ) -> list[dict[str, object]]:
        _ = dataset
        _ = schema
        _ = end_date
        return build_mock_historical_rows(symbol=symbol)


@dataclass(frozen=True)
class DatabentoHistoricalRowProvider(HistoricalRowProvider):
    client: DatabentoLiveHistoricalRowClient
    source: str = "databento"

    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
        end_date: str | None = None,
    ) -> list[dict[str, object]]:
        return self.client.get_daily_rows(
            symbol=symbol,
            lookback_days=90,
            dataset=dataset,
            schema=schema,
            end_date=end_date,
        )


def build_historical_row_provider() -> HistoricalRowProvider:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        settings = _load_live_databento_settings()
        return DatabentoHistoricalRowProvider(
            client=DatabentoLiveHistoricalRowClient(
                settings=settings,
                fetch_rows=fetch_databento_daily_rows,
            )
        )

    return MockHistoricalRowProvider()


def get_historical_row_provider_name() -> str:
    return "databento" if get_runtime_mode() == "live" else "mock"


def get_historical_row_provider_source() -> str:
    return "databento" if get_runtime_mode() == "live" else "mock"
