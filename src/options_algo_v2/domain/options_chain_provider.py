from __future__ import annotations

from typing import Protocol

from options_algo_v2.domain.options_chain import OptionsChainSnapshot


class OptionsChainProvider(Protocol):
    def get_chain(self, *, symbol: str) -> OptionsChainSnapshot:
        ...
