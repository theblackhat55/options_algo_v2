from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.polygon_settings import PolygonSettings

JsonDict = dict[str, object]


def _default_fetch_json(url: str, timeout_seconds: float) -> JsonDict:
    attempts = 3
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            with urlopen(url, timeout=timeout_seconds) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            last_error = exc
            if attempt == attempts:
                break
            sleep(0.5 * attempt)

    raise RuntimeError(f"polygon fetch failed after {attempts} attempts: {last_error}")


@dataclass(frozen=True)
class PolygonLiveOptionsChainClient:
    settings: PolygonSettings | None = None
    fetch_json: Callable[[str, float], JsonDict] = _default_fetch_json
    source: str = "polygon"

    def get_chain(self, symbol: str) -> OptionsChainSnapshot:
        return self.get_chain_snapshot(symbol)

    def get_chain_snapshot(self, symbol: str) -> OptionsChainSnapshot:
        settings = self.settings or PolygonSettings.from_env()

        query = urlencode(
            {
                "limit": 250,
                "apiKey": settings.api_key,
            }
        )
        url = f"{settings.base_url}/v3/snapshot/options/{symbol}?{query}"
        payload = self.fetch_json(url, settings.timeout_seconds)
        return self.normalize_chain_payload(symbol=symbol, payload=payload)

    def normalize_chain_payload(
        self,
        *,
        symbol: str,
        payload: JsonDict,
    ) -> OptionsChainSnapshot:
        results = payload.get("results", [])
        if not isinstance(results, list):
            raise ValueError("results must be a list")

        as_of = str(
            payload.get("as_of")
            or payload.get("request_id")
            or "polygon_snapshot"
        )

        quotes: list[OptionQuote] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            quote = self._normalize_quote(symbol=symbol, item=item)
            if quote is not None:
                quotes.append(quote)

        return OptionsChainSnapshot(
            symbol=symbol,
            quotes=quotes,
            as_of=as_of,
            source=self.source,
        )

    def _normalize_quote(
        self,
        *,
        symbol: str,
        item: JsonDict,
    ) -> OptionQuote | None:
        details = item.get("details")
        if not isinstance(details, dict):
            return None

        contract_type = str(details.get("contract_type", "")).lower()
        if contract_type == "call":
            option_type = "CALL"
        elif contract_type == "put":
            option_type = "PUT"
        else:
            return None

        strike_price = details.get("strike_price")
        expiration_date = details.get("expiration_date")
        option_symbol = details.get("ticker")

        if strike_price is None or expiration_date is None or option_symbol is None:
            return None

        last_quote = item.get("last_quote")
        bid: float | None = None
        ask: float | None = None

        if isinstance(last_quote, dict):
            bid = self._to_float(last_quote.get("bid"))
            ask = self._to_float(last_quote.get("ask"))

        day = item.get("day")
        if (bid is None or ask is None) and isinstance(day, dict):
            close_price = self._to_float(day.get("close"))
            if close_price is not None:
                bid = close_price
                ask = close_price

        if bid is None or ask is None:
            return None

        greeks = item.get("greeks")
        delta = 0.0
        implied_volatility: float | None = None
        if isinstance(greeks, dict):
            delta = self._to_float(greeks.get("delta")) or 0.0
            implied_volatility = self._normalize_implied_vol(
                self._to_float(greeks.get("implied_volatility"))
                or self._to_float(greeks.get("iv"))
            )

        if implied_volatility is None:
            implied_volatility = self._normalize_implied_vol(
                self._to_float(item.get("implied_volatility"))
                or self._to_float(item.get("iv"))
            )

        open_interest = int(self._to_float(item.get("open_interest")) or 0.0)

        volume = 0
        if isinstance(day, dict):
            volume = int(self._to_float(day.get("volume")) or 0.0)

        strike = self._to_float(strike_price)
        if strike is None:
            return None

        mid = (bid + ask) / 2.0

        return OptionQuote(
            symbol=symbol,
            option_symbol=str(option_symbol),
            expiration=str(expiration_date),
            strike=strike,
            option_type=option_type,
            bid=bid,
            ask=ask,
            mid=mid,
            delta=delta,
            implied_volatility=implied_volatility,
            open_interest=open_interest,
            volume=volume,
        )

    @staticmethod
    def _normalize_implied_vol(value: float | None) -> float | None:
        if value is None or value <= 0:
            return None
        if value > 3.0:
            return value / 100.0
        return value

    @staticmethod
    def _to_float(value: object) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return float(stripped)
            except ValueError:
                return None
        return None
