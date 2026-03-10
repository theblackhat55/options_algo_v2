import pytest

from options_algo_v2.services import databento_historical_fetcher


def test_fetch_databento_daily_rows_raises_when_sdk_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> list[dict[str, object]]:
        _ = self
        _ = symbol
        _ = dataset
        _ = schema
        raise RuntimeError("databento package is not installed")

    monkeypatch.setattr(
        databento_historical_fetcher.DatabentoHistoricalClientWrapper,
        "get_bar_rows",
        fake_get_bar_rows,
    )

    with pytest.raises(RuntimeError, match="databento package is not installed"):
        databento_historical_fetcher.fetch_databento_daily_rows(
            symbol="AAPL",
            lookback_days=50,
            dataset="XNAS.ITCH",
            schema="ohlcv-1d",
            api_key="test-key",
        )
