from __future__ import annotations

import pytest

from options_algo_v2.adapters.live_historical_row_client import (
    PlaceholderLiveHistoricalRowClient,
)


def test_placeholder_live_historical_row_client_has_source() -> None:
    client = PlaceholderLiveHistoricalRowClient()

    assert client.source == "live_historical_placeholder"


def test_placeholder_live_historical_row_client_raises_not_implemented() -> None:
    client = PlaceholderLiveHistoricalRowClient()

    with pytest.raises(
        NotImplementedError,
        match="live historical row client is not implemented",
    ):
        client.get_daily_bars(
            symbol="AAPL",
            lookback_days=50,
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
        )
