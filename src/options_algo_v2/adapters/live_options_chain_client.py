from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.domain.options_chain import OptionsChainSnapshot


@dataclass(frozen=True)
class PlaceholderLiveOptionsChainClient:
    source: str = "live_options_placeholder"

    def get_chain(self, *, symbol: str) -> OptionsChainSnapshot:
        del symbol
        raise NotImplementedError("live options chain client is not implemented")
