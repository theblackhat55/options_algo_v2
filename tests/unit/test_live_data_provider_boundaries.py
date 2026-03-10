from __future__ import annotations

import pytest

from options_algo_v2.services.historical_row_provider_factory import (
    build_historical_row_provider,
)
from options_algo_v2.services.market_breadth_provider_factory import (
    build_market_breadth_provider,
)


def test_live_historical_provider_requires_databento_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    with pytest.raises(
        ValueError,
        match="DATABENTO_API_KEY is required for live runtime mode",
    ):
        build_historical_row_provider()


def test_live_market_breadth_provider_placeholder_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")

    provider = build_market_breadth_provider()

    with pytest.raises(
        NotImplementedError,
        match="live market breadth client is not implemented",
    ):
        provider.get_pct_above_20dma(symbol="AAPL")
