from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.adapters.databento_sdk_client import DatabentoHistoricalClientWrapper
from options_algo_v2.domain.historical_row_provider import HistoricalRowProvider
from options_algo_v2.services.databento_settings import load_databento_settings
from options_algo_v2.services.mock_historical_rows import build_mock_historical_rows
from options_algo_v2.services.runtime_mode import get_runtime_mode


@dataclass(frozen=True)
class MockHistoricalRowProvider:
    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> list[dict[str, object]]:
        del dataset, schema
        return build_mock_historical_rows(symbol)


@dataclass(frozen=True)
class DatabentoHistoricalRowProvider:
    client_wrapper: DatabentoHistoricalClientWrapper

    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> list[dict[str, object]]:
        return self.client_wrapper.get_bar_rows(
            symbol=symbol,
            dataset=dataset,
            schema=schema,
        )


def build_historical_row_provider() -> HistoricalRowProvider:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        settings = load_databento_settings()
        return DatabentoHistoricalRowProvider(
            client_wrapper=DatabentoHistoricalClientWrapper(api_key=settings.api_key)
        )

    return MockHistoricalRowProvider()


def get_historical_row_provider_name() -> str:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        return "databento"

    return "mock"
