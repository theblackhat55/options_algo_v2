from __future__ import annotations


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
                "high": close + 1.0,
                "low": close - 3.0,
                "close": close,
                "volume": 1_000_000 + index * 1_000,
            }
        )
    return rows


def _build_pass_series() -> list[float]:
    first_segment = [100.0 + day for day in range(30)]
    second_segment = [130.0 + 0.25 * day for day in range(19)]
    final_close = 135.0
    return first_segment + second_segment + [final_close]


def _build_extended_series() -> list[float]:
    first_segment = [100.0 + day for day in range(30)]
    second_segment = [130.0 + 0.5 * day for day in range(19)]
    final_close = 142.0
    return first_segment + second_segment + [final_close]


def _build_neutral_series() -> list[float]:
    return [100.0 + (day % 5) for day in range(50)]
