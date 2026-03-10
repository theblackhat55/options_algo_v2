from __future__ import annotations

from options_algo_v2.adapters.databento_sdk_client import (
    DatabentoHistoricalClientWrapper,
)
from options_algo_v2.services.databento_settings import load_databento_settings


class DatabentoLiveClient:
    def __init__(
        self,
        api_key: str,
        sdk_wrapper: DatabentoHistoricalClientWrapper | None = None,
    ) -> None:
        self.api_key = api_key
        self._sdk_wrapper = sdk_wrapper or DatabentoHistoricalClientWrapper(
            api_key=api_key,
        )

    def get_underlying_snapshot(self, symbol: str) -> dict[str, object]:
        settings = load_databento_settings()

        return self._sdk_wrapper.get_underlying_snapshot(
            symbol=symbol,
            dataset=settings.dataset,
            schema=settings.schema,
        )
