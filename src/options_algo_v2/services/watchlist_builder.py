from __future__ import annotations

from dataclasses import asdict, dataclass

from options_algo_v2.services.historical_row_provider_factory import (
    HistoricalRowProvider,
)
from options_algo_v2.services.market_breadth_provider_factory import (
    MarketBreadthProvider,
)


@dataclass(frozen=True)
class WatchlistRow:
    symbol: str
    watchlist_score: float
    close: float
    sma20: float
    price_vs_20dma_pct: float
    avg_daily_volume: int
    trailing_20d_return_pct: float
    trailing_20d_range_pct: float
    market_breadth_pct_above_20dma: float
    source_dataset: str
    source_schema: str
    historical_row_provider: str
    market_breadth_provider: str


def _to_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return float(stripped)
        except ValueError:
            return default
    return default


def _to_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return int(float(stripped))
        except ValueError:
            return default
    return default


def _sma(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _build_watchlist_row(
    *,
    symbol: str,
    raw_rows: list[dict[str, object]],
    market_breadth_pct_above_20dma: float,
    dataset: str,
    schema: str,
    historical_row_provider_name: str,
    market_breadth_provider_name: str,
) -> WatchlistRow:
    closes = [_to_float(row.get("close"), 0.0) for row in raw_rows]
    highs = [_to_float(row.get("high"), 0.0) for row in raw_rows]
    lows = [_to_float(row.get("low"), 0.0) for row in raw_rows]
    volumes = [_to_int(row.get("volume"), 0) for row in raw_rows]

    if len(closes) < 20:
        raise ValueError(f"need at least 20 rows for watchlist scoring: {symbol}")

    close = closes[-1]
    sma20 = _sma(closes[-20:])
    avg_daily_volume = int(_sma([float(v) for v in volumes[-20:]]))

    reference_close = closes[-20]
    trailing_20d_return_pct = 0.0
    if reference_close > 0:
        trailing_20d_return_pct = ((close - reference_close) / reference_close) * 100.0

    trailing_20d_range_pct = 0.0
    valid_highs = highs[-20:]
    valid_lows = lows[-20:]
    if close > 0 and valid_highs and valid_lows:
        highest = max(valid_highs)
        lowest = min(valid_lows)
        trailing_20d_range_pct = ((highest - lowest) / close) * 100.0

    price_vs_20dma_pct = 0.0
    if sma20 > 0:
        price_vs_20dma_pct = ((close - sma20) / sma20) * 100.0

    volume_score = min(avg_daily_volume / 5_000_000.0, 1.0) * 30.0
    trend_score = min(max(trailing_20d_return_pct, 0.0) / 15.0, 1.0) * 30.0
    extension_score = max(0.0, 20.0 - min(abs(price_vs_20dma_pct), 20.0))
    movement_score = min(trailing_20d_range_pct / 20.0, 1.0) * 20.0

    watchlist_score = round(
        volume_score + trend_score + extension_score + movement_score,
        3,
    )

    return WatchlistRow(
        symbol=symbol,
        watchlist_score=watchlist_score,
        close=round(close, 4),
        sma20=round(sma20, 4),
        price_vs_20dma_pct=round(price_vs_20dma_pct, 4),
        avg_daily_volume=avg_daily_volume,
        trailing_20d_return_pct=round(trailing_20d_return_pct, 4),
        trailing_20d_range_pct=round(trailing_20d_range_pct, 4),
        market_breadth_pct_above_20dma=round(market_breadth_pct_above_20dma, 4),
        source_dataset=dataset,
        source_schema=schema,
        historical_row_provider=historical_row_provider_name,
        market_breadth_provider=market_breadth_provider_name,
    )


def build_watchlist_rows(
    *,
    symbols: list[str],
    historical_row_provider: HistoricalRowProvider,
    market_breadth_provider: MarketBreadthProvider,
    dataset: str,
    schema: str,
    historical_row_provider_name: str,
    market_breadth_provider_name: str,
    end_date: str | None = None,
) -> list[WatchlistRow]:
    rows: list[WatchlistRow] = []

    for symbol in symbols:
        historical_rows = historical_row_provider.get_bar_rows(
            symbol=symbol,
            dataset=dataset,
            schema=schema,
            end_date=end_date,
        )
        market_breadth_pct_above_20dma = _to_float(
            market_breadth_provider.get_pct_above_20dma(symbol=symbol),
            0.0,
        )

        rows.append(
            _build_watchlist_row(
                symbol=symbol,
                raw_rows=historical_rows,
                market_breadth_pct_above_20dma=market_breadth_pct_above_20dma,
                dataset=dataset,
                schema=schema,
                historical_row_provider_name=historical_row_provider_name,
                market_breadth_provider_name=market_breadth_provider_name,
            )
        )

    return sorted(
        rows,
        key=lambda item: item.watchlist_score,
        reverse=True,
    )


def serialize_watchlist_rows(rows: list[WatchlistRow]) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]
