from __future__ import annotations

import pytest

from options_algo_v2.services.market_breadth_provider_factory import (
    build_market_breadth_provider,
)


def test_live_market_breadth_provider_raises_when_source_unconfigured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "live")
    monkeypatch.delenv("OPTIONS_ALGO_MARKET_BREADTH_URL", raising=False)
    monkeypatch.delenv("OPTIONS_ALGO_MARKET_BREADTH_STATIC_PCT_ABOVE_20DMA", raising=False)
    monkeypatch.delenv("OPTIONS_ALGO_MARKET_BREADTH_STATIC_TIMESTAMP", raising=False)

    provider = build_market_breadth_provider()

    with pytest.raises(
        RuntimeError,
        match="live market breadth data source is not configured",
    ):
        provider.get_pct_above_20dma(symbol="AAPL")
