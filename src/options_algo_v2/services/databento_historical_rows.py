from __future__ import annotations

from options_algo_v2.adapters.databento_sdk_client import (
    DatabentoHistoricalClientWrapper,
)


def fetch_historical_bar_rows(
    *,
    symbol: str,
    dataset: str,
    schema: str,
    client_wrapper: DatabentoHistoricalClientWrapper,
) -> list[dict[str, object]]:
    rows = client_wrapper.get_bar_rows(
        symbol=symbol,
        dataset=dataset,
        schema=schema,
    )

    if not rows:
        raise ValueError(f"no historical bar rows returned for symbol={symbol}")

    return rows
