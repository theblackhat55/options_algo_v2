from __future__ import annotations

from collections.abc import Callable

from options_algo_v2.domain.options_data import OptionSnapshot


class PolygonOptionsAdapter:
    def __init__(
        self,
        fetcher: Callable[[str], dict[str, object]],
    ) -> None:
        self._fetcher = fetcher

    def get_snapshot(
        self,
        option_symbol: str,
    ) -> OptionSnapshot:
        payload = self._fetcher(option_symbol)

        underlying_symbol = payload.get("underlying_symbol")
        strike = payload.get("strike")
        right = payload.get("right")
        expiry = payload.get("expiry")
        bid = payload.get("bid")
        ask = payload.get("ask")
        iv = payload.get("iv")
        delta = payload.get("delta")
        open_interest = payload.get("open_interest")
        volume = payload.get("volume")
        quote_timestamp = payload.get("quote_timestamp")

        if not isinstance(underlying_symbol, str):
            msg = "underlying_symbol must be a string"
            raise ValueError(msg)

        if not isinstance(strike, (int, float)):
            msg = "strike must be numeric"
            raise ValueError(msg)

        if not isinstance(right, str):
            msg = "right must be a string"
            raise ValueError(msg)

        if right not in {"C", "P"}:
            msg = "right must be C or P"
            raise ValueError(msg)

        if not isinstance(expiry, str):
            msg = "expiry must be a string"
            raise ValueError(msg)

        if not isinstance(bid, (int, float)):
            msg = "bid must be numeric"
            raise ValueError(msg)

        if not isinstance(ask, (int, float)):
            msg = "ask must be numeric"
            raise ValueError(msg)

        if not isinstance(iv, (int, float)):
            msg = "iv must be numeric"
            raise ValueError(msg)

        if not isinstance(delta, (int, float)):
            msg = "delta must be numeric"
            raise ValueError(msg)

        if not isinstance(open_interest, int):
            msg = "open_interest must be an integer"
            raise ValueError(msg)

        if not isinstance(volume, int):
            msg = "volume must be an integer"
            raise ValueError(msg)

        if not isinstance(quote_timestamp, str):
            msg = "quote_timestamp must be a string"
            raise ValueError(msg)

        return OptionSnapshot(
            underlying_symbol=underlying_symbol.upper(),
            option_symbol=option_symbol.upper(),
            strike=float(strike),
            right=right,
            expiry=expiry,
            bid=float(bid),
            ask=float(ask),
            iv=float(iv),
            delta=float(delta),
            open_interest=open_interest,
            volume=volume,
            quote_timestamp=quote_timestamp,
        )
