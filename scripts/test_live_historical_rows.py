from __future__ import annotations

import sys

from options_algo_v2.services.databento_settings import load_databento_settings
from options_algo_v2.services.historical_row_provider_factory import (
    build_historical_row_provider,
    get_historical_row_provider_name,
    get_historical_row_provider_source,
)


def main() -> None:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    settings = load_databento_settings()
    provider = build_historical_row_provider()

    rows = provider.get_bar_rows(
        symbol=symbol,
        dataset=settings.dataset,
        schema=settings.schema,
    )

    print(f"provider={get_historical_row_provider_name()}")
    print(f"provider_source={get_historical_row_provider_source()}")
    print(f"symbol={symbol}")
    print(f"dataset={settings.dataset}")
    print(f"schema={settings.schema}")
    print(f"rows={len(rows)}")

    if not rows:
        print("No rows returned.")
        return

    first_row = rows[0]
    last_row = rows[-1]

    print(f"first_ts={first_row.get('ts_event')}")
    print(f"last_ts={last_row.get('ts_event')}")
    print(f"last_close={last_row.get('close')}")


if __name__ == "__main__":
    main()
