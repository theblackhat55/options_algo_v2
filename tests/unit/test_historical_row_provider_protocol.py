from options_algo_v2.domain.historical_row_provider import HistoricalRowProvider
from options_algo_v2.services.historical_row_provider_factory import (
    MockHistoricalRowProvider,
)


def test_mock_historical_row_provider_matches_protocol() -> None:
    provider: HistoricalRowProvider = MockHistoricalRowProvider()

    rows = provider.get_bar_rows(
        symbol="AAPL",
        dataset="XNAS.ITCH",
        schema="ohlcv-1d",
    )

    assert len(rows) == 50
    assert rows[0]["ts_event"] == "2026-03-01T21:00:00Z"
    assert "open" in rows[0]
    assert "high" in rows[0]
    assert "low" in rows[0]
    assert "close" in rows[0]
    assert "volume" in rows[0]
