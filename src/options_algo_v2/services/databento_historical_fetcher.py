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
    wrapper = DatabentoHistoricalClientWrapper(api_key=api_key)
    try:
        rows = wrapper.get_bar_rows(
            symbol=symbol,
            dataset=dataset,
            schema=schema,
            lookback_days=lookback_days,
        )
    except TypeError as exc:
        if "lookback_days" not in str(exc):
            raise
        rows = wrapper.get_bar_rows(
            symbol=symbol,
            dataset=dataset,
            schema=schema,
        )

    if not rows:
        raise ValueError(
            "no databento rows returned "
            f"for symbol={symbol}, dataset={dataset}, schema={schema}"
        )

    return rows
