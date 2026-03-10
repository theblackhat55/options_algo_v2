from __future__ import annotations

from options_algo_v2.adapters.databento_sdk_client import (
    DatabentoHistoricalClientWrapper,
)


def fetch_databento_daily_rows(
    symbol: str,
    lookback_days: int,
    dataset: str,
    schema: str,
    api_key: str,
) -> list[dict[str, object]]:
    _ = lookback_days
    wrapper = DatabentoHistoricalClientWrapper(api_key=api_key)
    return wrapper.get_bar_rows(
        symbol=symbol,
        dataset=dataset,
        schema=schema,
    )
