from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.polygon_settings import PolygonSettings


@dataclass(frozen=True)
class PolygonLiveOptionsChainClient:
    settings: PolygonSettings
    source: str = "polygon"

    def get_chain(self, *, symbol: str) -> OptionsChainSnapshot:
        del symbol
        raise NotImplementedError("polygon live options chain client is not implemented")

    def normalize_chain_payload(
        self,
        *,
        symbol: str,
        payload: dict[str, object],
    ) -> OptionsChainSnapshot:
        results = payload.get("results", [])
        if not isinstance(results, list):
            raise ValueError("polygon payload results must be a list")

        quotes: list[OptionQuote] = []
        for item in results:
            if not isinstance(item, dict):
                raise ValueError("polygon payload result item must be a dict")

            details = item.get("details", {})
            last_quote = item.get("last_quote", {})
            greeks = item.get("greeks", {})
            day = item.get("day", {})

            if not isinstance(details, dict):
                raise ValueError("polygon payload details must be a dict")
            if not isinstance(last_quote, dict):
                raise ValueError("polygon payload last_quote must be a dict")
            if not isinstance(greeks, dict):
                raise ValueError("polygon payload greeks must be a dict")
            if not isinstance(day, dict):
                raise ValueError("polygon payload day must be a dict")

            strike_price = float(details["strike_price"])
            bid = float(last_quote["bid"])
            ask = float(last_quote["ask"])
            mid = (bid + ask) / 2.0
            delta = greeks.get("delta")
            normalized_delta = float(delta) if delta is not None else None
            open_interest = int(item.get("open_interest", 0))
            volume = int(day.get("volume", 0))

            quotes.append(
                OptionQuote(
                    symbol=symbol,
                    option_symbol=str(details["ticker"]),
                    expiration=str(details["expiration_date"]),
                    strike=strike_price,
                    option_type=str(details["contract_type"]),
                    bid=bid,
                    ask=ask,
                    mid=mid,
                    delta=normalized_delta,
                    open_interest=open_interest,
                    volume=volume,
                )
            )

        return OptionsChainSnapshot(
            symbol=symbol,
            quotes=quotes,
            as_of=str(payload.get("as_of", "")),
            source=self.source,
        )
