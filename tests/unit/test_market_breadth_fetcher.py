from __future__ import annotations

import pytest

from options_algo_v2.services.market_breadth_fetcher import (
    fetch_live_market_breadth_payload,
)


def test_fetch_live_market_breadth_payload_raises_when_unconfigured() -> None:
    with pytest.raises(
        RuntimeError,
        match="live market breadth data source is not configured",
    ):
        fetch_live_market_breadth_payload()
