from options_algo_v2.services.feature_source_diagnostics import (
    count_feature_sources_by_dataset_schema,
    count_feature_sources_by_historical_row_provider,
    count_feature_sources_by_market_breadth_provider,
)


def test_count_feature_sources_by_historical_row_provider() -> None:
    feature_sources = [
        {
            "symbol": "AAPL",
            "historical_row_provider": "mock",
            "market_breadth_provider": "mock",
            "dataset": "XNAS.ITCH",
            "schema": "ohlcv-1d",
        },
        {
            "symbol": "SPY",
            "historical_row_provider": "databento",
            "market_breadth_provider": "live",
            "dataset": "GLBX.MDP3",
            "schema": "ohlcv-1m",
        },
        {
            "symbol": "MSFT",
            "historical_row_provider": "mock",
            "market_breadth_provider": "mock",
            "dataset": "XNAS.ITCH",
            "schema": "ohlcv-1d",
        },
    ]

    assert count_feature_sources_by_historical_row_provider(feature_sources) == {
        "mock": 2,
        "databento": 1,
    }


def test_count_feature_sources_by_market_breadth_provider() -> None:
    feature_sources = [
        {
            "symbol": "AAPL",
            "historical_row_provider": "mock",
            "market_breadth_provider": "mock",
            "dataset": "XNAS.ITCH",
            "schema": "ohlcv-1d",
        },
        {
            "symbol": "SPY",
            "historical_row_provider": "databento",
            "market_breadth_provider": "live",
            "dataset": "GLBX.MDP3",
            "schema": "ohlcv-1m",
        },
        {
            "symbol": "MSFT",
            "historical_row_provider": "mock",
            "market_breadth_provider": "mock",
            "dataset": "XNAS.ITCH",
            "schema": "ohlcv-1d",
        },
    ]

    assert count_feature_sources_by_market_breadth_provider(feature_sources) == {
        "mock": 2,
        "live": 1,
    }


def test_count_feature_sources_by_dataset_schema() -> None:
    feature_sources = [
        {
            "symbol": "AAPL",
            "historical_row_provider": "mock",
            "market_breadth_provider": "mock",
            "dataset": "XNAS.ITCH",
            "schema": "ohlcv-1d",
        },
        {
            "symbol": "SPY",
            "historical_row_provider": "databento",
            "market_breadth_provider": "live",
            "dataset": "GLBX.MDP3",
            "schema": "ohlcv-1m",
        },
        {
            "symbol": "MSFT",
            "historical_row_provider": "mock",
            "market_breadth_provider": "mock",
            "dataset": "XNAS.ITCH",
            "schema": "ohlcv-1d",
        },
    ]

    assert count_feature_sources_by_dataset_schema(feature_sources) == {
        "XNAS.ITCH|ohlcv-1d": 2,
        "GLBX.MDP3|ohlcv-1m": 1,
    }
