from __future__ import annotations

from typing import cast

from options_algo_v2.domain.bar_data import BarData


def build_bar_data_history(rows: list[dict[str, object]]) -> list[BarData]:
    if not rows:
        raise ValueError("no rows provided to build bar history")

    bars: list[BarData] = []

    for row in rows:
        if "ts_event" not in row:
            raise ValueError("missing 'ts_event' in bar row")
        if "open" not in row:
            raise ValueError("missing 'open' in bar row")
        if "high" not in row:
            raise ValueError("missing 'high' in bar row")
        if "low" not in row:
            raise ValueError("missing 'low' in bar row")
        if "close" not in row:
            raise ValueError("missing 'close' in bar row")
        if "volume" not in row:
            raise ValueError("missing 'volume' in bar row")

        timestamp = str(row["ts_event"])
        open_value = cast(float | int | str, row["open"])
        high_value = cast(float | int | str, row["high"])
        low_value = cast(float | int | str, row["low"])
        close_value = cast(float | int | str, row["close"])
        volume_value = cast(float | int | str, row["volume"])

        open_price = float(open_value)
        high = float(high_value)
        low = float(low_value)
        close = float(close_value)
        volume = float(volume_value)

        if high < low:
            raise ValueError("high cannot be below low in bar row")
        if open_price <= 0 or high <= 0 or low <= 0 or close <= 0:
            raise ValueError("ohlc values must be positive in bar row")
        if volume < 0:
            raise ValueError("volume cannot be negative in bar row")

        bars.append(
            BarData(
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
        )

    return bars
