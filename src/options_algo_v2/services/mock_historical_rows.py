from __future__ import annotations

import math


def build_mock_historical_rows(symbol: str) -> list[dict[str, object]]:
    pass_symbols = {"AAPL", "MSFT", "NVDA"}
    extended_symbols = {"SPY", "QQQ"}

    if symbol in pass_symbols:
        close_values = _build_pass_series()
    elif symbol in extended_symbols:
        close_values = _build_extended_series()
    else:
        close_values = _build_neutral_series()

    rows: list[dict[str, object]] = []
    for index, close in enumerate(close_values, start=1):
        rows.append(
            {
                "ts_event": f"2026-03-{index:02d}T21:00:00Z",
                "open": close - 1.0,
                "high": close + 1.5,
                "low": close - 2.0,
                "close": close,
                "volume": 1_000_000 + index * 1_000,
            }
        )
    return rows


def _build_pass_series() -> list[float]:
    """Slow uptrend with oscillations.

    Produces: close > dma20 > dma50, ADX >= 18, RSI in [45, 85],
    not extended — qualifies as BULLISH_CONTINUATION.
    """
    return [
        round(100.0 + i * 0.3 + 2.0 * math.sin(i * 0.9), 2)
        for i in range(50)
    ]


def _build_extended_series() -> list[float]:
    """Uptrend with a sharp final spike so close - dma20 > 2 * atr20."""
    base = [round(100.0 + i * 0.5, 2) for i in range(49)]
    return base + [base[-1] + 12.0]


def _build_neutral_series() -> list[float]:
    return [100.0 + (day % 5) for day in range(50)]
