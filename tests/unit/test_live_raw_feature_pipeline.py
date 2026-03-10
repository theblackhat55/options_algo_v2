from datetime import date

from options_algo_v2.domain.historical_row_provider import HistoricalRowProvider
from options_algo_v2.services.live_raw_feature_pipeline import (
    build_live_raw_feature_input,
)


class FakeHistoricalRowProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> list[dict[str, object]]:
        self.calls.append(
            {
                "symbol": symbol,
                "dataset": dataset,
                "schema": schema,
            }
        )

        rows: list[dict[str, object]] = []
        for day in range(50):
            close = 101.0 + day
            rows.append(
                {
                    "ts_event": f"2026-03-{day + 1:02d}T21:00:00Z",
                    "open": close - 1.0,
                    "high": close + 1.0,
                    "low": close - 3.0,
                    "close": close,
                    "volume": 1_000_000 + day * 1_000,
                }
            )
        return rows


def test_build_live_raw_feature_input_uses_provider_protocol() -> None:
    provider: HistoricalRowProvider = FakeHistoricalRowProvider()

    raw = build_live_raw_feature_input(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
        provider=provider,
        adx14=22.0,
        iv_rank=65.0,
        iv_hv_ratio=1.25,
        avg_daily_volume=5_000_000,
        option_open_interest=1_500,
        option_volume=800,
        bid=2.45,
        ask=2.65,
        option_quote_age_seconds=20.0,
        underlying_quote_age_seconds=10.0,
        market_breadth_pct_above_20dma=62.0,
        earnings_date=None,
        entry_date=date(2026, 3, 10),
        dte_days=35,
    )

    assert raw.symbol == "AAPL"
    assert raw.close == 150.0
    assert raw.dma20 == 140.5
    assert raw.dma50 == 125.5
    assert raw.atr20 == 4.0
    assert raw.adx14 == 22.0
    assert raw.iv_rank == 65.0
    assert raw.iv_hv_ratio == 1.25
    assert raw.avg_daily_volume == 5_000_000
    assert raw.option_open_interest == 1_500
    assert raw.option_volume == 800
    assert raw.bid == 2.45
    assert raw.ask == 2.65
    assert raw.market_breadth_pct_above_20dma == 62.0
