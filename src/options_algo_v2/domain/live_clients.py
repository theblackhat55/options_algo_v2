from __future__ import annotations

from typing import Protocol


class UnderlyingLiveClient(Protocol):
    def get_underlying_snapshot(self, symbol: str) -> dict[str, object]:
        ...
