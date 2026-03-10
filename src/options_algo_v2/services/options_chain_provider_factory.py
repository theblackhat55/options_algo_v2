from __future__ import annotations

from dataclasses import dataclass

from options_algo_v2.adapters.live_options_chain_client import (
    PolygonLiveOptionsChainClient,
)
from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.domain.options_chain_provider import OptionsChainProvider
from options_algo_v2.services.polygon_settings import load_polygon_settings
from options_algo_v2.services.runtime_mode import get_runtime_mode


@dataclass(frozen=True)
class MockOptionsChainProvider:
    def get_chain(self, *, symbol: str) -> OptionsChainSnapshot:
        quotes = [
            OptionQuote(
                symbol=symbol,
                option_symbol=f"{symbol}_20260417C00145000",
                expiration="2026-04-17",
                strike=145.0,
                option_type="call",
                bid=4.8,
                ask=5.2,
                mid=5.0,
                delta=0.42,
                open_interest=1200,
                volume=300,
            ),
            OptionQuote(
                symbol=symbol,
                option_symbol=f"{symbol}_20260417C00150000",
                expiration="2026-04-17",
                strike=150.0,
                option_type="call",
                bid=2.8,
                ask=3.2,
                mid=3.0,
                delta=0.31,
                open_interest=1100,
                volume=280,
            ),
            OptionQuote(
                symbol=symbol,
                option_symbol=f"{symbol}_20260417P00135000",
                expiration="2026-04-17",
                strike=135.0,
                option_type="put",
                bid=2.3,
                ask=2.7,
                mid=2.5,
                delta=-0.28,
                open_interest=1400,
                volume=320,
            ),
            OptionQuote(
                symbol=symbol,
                option_symbol=f"{symbol}_20260417P00130000",
                expiration="2026-04-17",
                strike=130.0,
                option_type="put",
                bid=1.3,
                ask=1.7,
                mid=1.5,
                delta=-0.19,
                open_interest=1000,
                volume=260,
            ),
        ]

        return OptionsChainSnapshot(
            symbol=symbol,
            quotes=quotes,
            as_of="2026-03-10T21:00:00Z",
            source="mock",
        )


@dataclass(frozen=True)
class LiveOptionsChainProvider:
    client: PolygonLiveOptionsChainClient

    def get_chain(self, *, symbol: str) -> OptionsChainSnapshot:
        return self.client.get_chain(symbol=symbol)


def build_options_chain_provider() -> OptionsChainProvider:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        settings = load_polygon_settings()
        return LiveOptionsChainProvider(
            client=PolygonLiveOptionsChainClient(settings=settings),
        )

    return MockOptionsChainProvider()


def get_options_chain_provider_name() -> str:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        return "polygon"

    return "mock"


def get_options_chain_provider_source() -> str:
    runtime_mode = get_runtime_mode()

    if runtime_mode == "live":
        return "polygon"

    return "mock"
