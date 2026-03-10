from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.adapters.polygon_live_options_chain_client import (
    PolygonLiveOptionsChainClient,
)
from options_algo_v2.domain.options_chain import OptionsChainSnapshot
from options_algo_v2.services.polygon_settings import get_polygon_api_key


@dataclass(frozen=True)
class PlaceholderLiveOptionsChainClient:
    def get_chain_snapshot(self, symbol: str) -> OptionsChainSnapshot:
        _ = symbol
        _ = get_polygon_api_key()
        raise NotImplementedError("live options chain client is not implemented")


__all__ = [
    "PlaceholderLiveOptionsChainClient",
    "PolygonLiveOptionsChainClient",
]
