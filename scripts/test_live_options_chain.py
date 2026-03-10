from __future__ import annotations

import sys

from options_algo_v2.services.options_chain_provider_factory import (
    build_options_chain_provider,
    get_options_chain_provider_name,
    get_options_chain_provider_source,
)


def main() -> None:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    provider = build_options_chain_provider()
    chain = provider.get_chain(symbol=symbol)

    quotes = list(chain.quotes)
    expirations = sorted({str(quote.expiration) for quote in quotes})
    call_count = sum(
        1 for quote in quotes if str(quote.option_type).upper() == "CALL"
    )
    put_count = sum(
        1 for quote in quotes if str(quote.option_type).upper() == "PUT"
    )

    print(f"provider={get_options_chain_provider_name()}")
    print(f"provider_source={get_options_chain_provider_source()}")
    print(f"symbol={symbol}")
    print(f"quotes={len(quotes)}")
    print(f"expirations={len(expirations)}")
    print(f"sample_expirations={expirations[:5]}")
    print(f"calls={call_count}")
    print(f"puts={put_count}")

    for index, quote in enumerate(quotes[:3], start=1):
        print(f"quote_{index}:")
        print(f"  symbol={quote.symbol}")
        print(f"  expiration={quote.expiration}")
        print(f"  strike={quote.strike}")
        print(f"  option_type={quote.option_type}")
        print(f"  bid={quote.bid}")
        print(f"  ask={quote.ask}")
        print(f"  delta={quote.delta}")
        print(f"  volume={quote.volume}")
        print(f"  open_interest={quote.open_interest}")


if __name__ == "__main__":
    main()
