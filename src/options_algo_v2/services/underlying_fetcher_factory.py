from __future__ import annotations

from collections.abc import Callable

from options_algo_v2.adapters.databento_live_client import DatabentoLiveClient
from options_algo_v2.domain.live_clients import UnderlyingLiveClient
from options_algo_v2.services.databento_env import get_databento_api_key
from options_algo_v2.services.runtime_mode import get_runtime_mode

LiveClientBuilder = Callable[[str], UnderlyingLiveClient]
UnderlyingFetcher = Callable[[str], dict[str, object]]


def build_databento_live_client(api_key: str) -> UnderlyingLiveClient:
    return DatabentoLiveClient(api_key=api_key)


def _mock_underlying_fetcher(symbol: str) -> dict[str, object]:
    bullish_prices = {
        "AAPL": 210.0,
        "MSFT": 420.0,
        "NVDA": 140.0,
        "META": 500.0,
        "SPY": 520.0,
        "QQQ": 450.0,
    }

    close = bullish_prices.get(symbol.upper(), 100.0)
    volume = 5_000_000 if symbol.upper() in bullish_prices else 2_000_000

    return {
        "close": close,
        "volume": volume,
        "timestamp": "2026-03-10T21:00:00Z",
    }


def _build_live_underlying_fetcher(
    client_builder: LiveClientBuilder | None = None,
) -> UnderlyingFetcher:
    api_key = get_databento_api_key()
    builder = client_builder or build_databento_live_client
    client = builder(api_key)

    def _live_underlying_fetcher(symbol: str) -> dict[str, object]:
        return client.get_underlying_snapshot(symbol)

    return _live_underlying_fetcher


def build_underlying_fetcher(
    client_builder: LiveClientBuilder | None = None,
) -> UnderlyingFetcher:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        return _build_live_underlying_fetcher(client_builder=client_builder)

    return _mock_underlying_fetcher
