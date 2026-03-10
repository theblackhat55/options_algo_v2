from __future__ import annotations

from collections.abc import Callable

from options_algo_v2.domain.underlying_data import UnderlyingSnapshot


class DatabentoUnderlyingAdapter:
    def __init__(
        self,
        fetcher: Callable[[str], dict[str, object]],
    ) -> None:
        self._fetcher = fetcher

    def get_snapshot(
        self,
        symbol: str,
    ) -> UnderlyingSnapshot:
        payload = self._fetcher(symbol)

        close = payload.get("close")
        volume = payload.get("volume")
        timestamp = payload.get("timestamp")

        if not isinstance(close, (int, float)):
            msg = "close must be numeric"
            raise ValueError(msg)

        if not isinstance(volume, (int, float)):
            msg = "volume must be numeric"
            raise ValueError(msg)

        if not isinstance(timestamp, str):
            msg = "timestamp must be a string"
            raise ValueError(msg)

        return UnderlyingSnapshot(
            symbol=symbol.upper(),
            close=float(close),
            volume=float(volume),
            timestamp=timestamp,
        )
