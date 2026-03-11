from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from scripts.run_nightly_scan import run_nightly_scan
except ImportError:
    from run_nightly_scan import run_nightly_scan


def _parse_args(argv: list[str]) -> tuple[list[str] | None, str | None]:
    if not argv:
        return None, None

    if argv[0] == "--watchlist":
        if len(argv) < 2:
            raise ValueError("--watchlist requires a path")
        return None, argv[1]

    return argv, None


def run_trade_ideas(
    symbols: list[str] | None = None,
    watchlist_path: str | None = None,
) -> str:
    output_path = run_nightly_scan(
        symbols=symbols,
        watchlist_path=watchlist_path,
    )

    payload = json.loads(Path(output_path).read_text())

    summary = payload["summary"]
    runtime_metadata = payload["runtime_metadata"]
    trade_ideas = payload.get("trade_ideas", [])

    print(
        "summary="
        f"total={summary['total_candidates']},"
        f"passed={summary['total_passed']},"
        f"rejected={summary['total_rejected']}"
    )
    print(f"trade_idea_count={runtime_metadata.get('trade_idea_count', 0)}")
    print(f"trade_idea_symbols={runtime_metadata.get('trade_idea_symbols', [])}")

    for index, idea in enumerate(trade_ideas, start=1):
        print(f"trade_idea_{index}:")
        print(f"  symbol={idea.get('symbol')}")
        print(f"  strategy={idea.get('strategy_family')}")
        print(f"  expiration={idea.get('expiration')}")
        print(f"  short_leg_symbol={idea.get('short_leg_option_symbol')}")
        print(f"  short_leg_strike={idea.get('short_strike')}")
        print(f"  long_leg_symbol={idea.get('long_leg_option_symbol')}")
        print(f"  long_leg_strike={idea.get('long_strike')}")
        print(f"  net_credit={idea.get('net_credit')}")
        print(f"  net_debit={idea.get('net_debit')}")
        print(f"  width={idea.get('width')}")
        print(f"  max_risk={idea.get('max_risk')}")
        print(f"  score={idea.get('score')}")
        print(f"  market_regime={idea.get('market_regime')}")
        print(f"  directional_state={idea.get('directional_state')}")
        print(f"  iv_state={idea.get('iv_state')}")

    return output_path


if __name__ == "__main__":
    parsed_symbols, parsed_watchlist = _parse_args(sys.argv[1:])
    run_trade_ideas(
        symbols=parsed_symbols,
        watchlist_path=parsed_watchlist,
    )
