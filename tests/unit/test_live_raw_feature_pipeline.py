from datetime import date

from options_algo_v2.services.live_raw_feature_pipeline import (
    build_live_raw_feature_input,
)


class FakeWrapper:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows
        self.calls: list[dict[str, object]] = []

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
        return self.rows


def _make_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for index in range(50):
        close = float(index + 101)
        rows.append(
            {
                "ts_event": f"2026-03-{(index % 28) + 1:02d}T21:00:00Z",
                "open": close,
                "high": close + 2.0,
                "low": close - 2.0,
                "close": close,
                "volume": 1_000_000 + index,
            }
        )

    return rows


def test_build_live_raw_feature_input_returns_expected_model() -> None:
    wrapper = FakeWrapper(rows=_make_rows())

    raw = build_live_raw_feature_input(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
        client_wrapper=wrapper,
        adx14=22.0,
        iv_rank=65.0,
        iv_hv_ratio=1.30,
        avg_daily_volume=5_000_000,
        option_open_interest=2_000,
        option_volume=400,
        bid=2.45,
        ask=2.55,
        option_quote_age_seconds=10,
        underlying_quote_age_seconds=2,
        market_breadth_pct_above_20dma=60.0,
        earnings_date=None,
        entry_date=date(2026, 3, 10),
        dte_days=35,
    )

    assert wrapper.calls == [
        {
            "symbol": "AAPL",
            "dataset": "XNAS.ITCH",
            "schema": "ohlcv-1d",
        }
    ]
    assert raw.symbol == "AAPL"
    assert raw.close == 150.0
    assert raw.dma20 == 140.5
    assert raw.dma50 == 125.5
    assert raw.atr20 == 4.0
    assert raw.adx14 == 22.0
    assert raw.iv_rank == 65.0
    assert raw.iv_hv_ratio == 1.30
    assert raw.avg_daily_volume == 5_000_000
    assert raw.option_open_interest == 2_000
    assert raw.option_volume == 400
    assert raw.bid == 2.45
    assert raw.ask == 2.55
    assert raw.option_quote_age_seconds == 10
    assert raw.underlying_quote_age_seconds == 2
    assert raw.market_breadth_pct_above_20dma == 60.0
    assert raw.earnings_date is None
    assert raw.entry_date == date(2026, 3, 10)
    assert raw.dte_days == 35
