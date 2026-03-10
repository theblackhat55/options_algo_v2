from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.adapters.live_options_chain_client import (
    PlaceholderLiveOptionsChainClient,
)
from options_algo_v2.adapters.polygon_live_options_chain_client import (
    PolygonLiveOptionsChainClient,
)
from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.domain.options_chain_provider import OptionsChainProvider
from options_algo_v2.services.polygon_settings import (
    PolygonSettings,
    has_polygon_api_key,
)
from options_algo_v2.services.runtime_mode import get_runtime_mode


@dataclass(frozen=True)
class MockOptionsChainProvider:
    def get_chain(self, symbol: str) -> OptionsChainSnapshot:
        quotes = [
            OptionQuote(
                symbol=symbol,
                option_symbol=f"{symbol}_2026-04-17_C_100",
                expiration="2026-04-17",
                strike=100.0,
                option_type="CALL",
                bid=2.40,
                ask=2.60,
                mid=2.50,
                delta=0.35,
                open_interest=1_500,
                volume=250,
            ),
            OptionQuote(
                symbol=symbol,
                option_symbol=f"{symbol}_2026-04-17_C_105",
                expiration="2026-04-17",
                strike=105.0,
                option_type="CALL",
                bid=1.40,
                ask=1.60,
                mid=1.50,
                delta=0.22,
                open_interest=1_200,
                volume=200,
            ),
            OptionQuote(
                symbol=symbol,
                option_symbol=f"{symbol}_2026-04-17_P_95",
                expiration="2026-04-17",
                strike=95.0,
                option_type="PUT",
                bid=1.40,
                ask=1.60,
                mid=1.50,
                delta=-0.22,
                open_interest=1_200,
                volume=200,
            ),
            OptionQuote(
                symbol=symbol,
                option_symbol=f"{symbol}_2026-04-17_P_100",
                expiration="2026-04-17",
                strike=100.0,
                option_type="PUT",
                bid=2.40,
                ask=2.60,
                mid=2.50,
                delta=-0.35,
                open_interest=1_500,
                volume=250,
            ),
        ]
        return OptionsChainSnapshot(
            symbol=symbol,
            quotes=quotes,
            as_of="2026-03-10T00:00:00Z",
            source="mock",
        )


@dataclass(frozen=True)
class LiveOptionsChainProvider:
    client: PolygonLiveOptionsChainClient

    def get_chain(self, symbol: str) -> OptionsChainSnapshot:
        return self.client.get_chain_snapshot(symbol)


def build_options_chain_provider() -> OptionsChainProvider:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        if not has_polygon_api_key():
            raise ValueError("POLYGON_API_KEY is required for live options chain mode")
        return LiveOptionsChainProvider(
            client=PolygonLiveOptionsChainClient(settings=PolygonSettings.from_env())
        )

    return MockOptionsChainProvider()


def get_options_chain_provider_name() -> str:
    return "polygon" if get_runtime_mode() == "live" else "mock"


def get_options_chain_provider_source() -> str:
    return "polygon" if get_runtime_mode() == "live" else "mock"


def build_placeholder_live_options_chain_client() -> PlaceholderLiveOptionsChainClient:
    return PlaceholderLiveOptionsChainClient()
