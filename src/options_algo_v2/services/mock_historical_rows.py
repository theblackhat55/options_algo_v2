from __future__ import annotations


def build_mock_historical_rows(symbol: str) -> list[dict[str, object]]:
    pass_symbols = {"AAPL", "MSFT", "NVDA"}
    extended_symbols = {"SPY", "QQQ"}
    close_start = 101.0

    rows: list[dict[str, object]] = []

    for index in range(50):
        close = close_start + index

        if symbol in pass_symbols:
            adjusted_close = close + 50.0
        elif symbol in extended_symbols:
            adjusted_close = close + 50.0
        else:
            adjusted_close = close

        rows.append(
            {
                "ts_event": f"2026-03-{(index % 28) + 1:02d}T21:00:00Z",
                "open": adjusted_close,
                "high": adjusted_close + 2.0,
                "low": adjusted_close - 2.0,
                "close": adjusted_close,
                "volume": 1_000_000 + index,
            }
        )

    return rows
