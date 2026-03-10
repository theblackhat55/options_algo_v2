from __future__ import annotations

import json
from pathlib import Path

from scripts.run_nightly_scan import run_nightly_scan


def run_trade_ideas() -> str:
    output_path = run_nightly_scan()
    path = Path(output_path)
    payload = json.loads(path.read_text())

    summary = payload.get("summary", {})
    runtime_metadata = payload.get("runtime_metadata", {})
    trade_ideas = payload.get("trade_ideas", [])

    print(
        "summary="
        f"total={summary.get('total_candidates', 0)},"
        f"passed={summary.get('total_passed', 0)},"
        f"rejected={summary.get('total_rejected', 0)}"
    )
    print(f"trade_idea_count={runtime_metadata.get('trade_idea_count', 0)}")
    print(f"trade_idea_symbols={runtime_metadata.get('trade_idea_symbols', [])}")

    for index, idea in enumerate(trade_ideas, start=1):
        print(f"{index}) {idea.get('symbol', 'UNKNOWN')}")
        print(f"   strategy={idea.get('strategy_family', 'UNKNOWN')}")
        print(f"   expiration={idea.get('expiration', '')}")
        print(f"   option_type={idea.get('option_type', '')}")
        print(
            "   short_leg="
            f"{idea.get('short_leg_option_symbol', '')}"
            f" @ {idea.get('short_strike', 0.0)}"
        )
        print(
            "   long_leg="
            f"{idea.get('long_leg_option_symbol', '')}"
            f" @ {idea.get('long_strike', 0.0)}"
        )
        print(f"   net_credit={idea.get('net_credit', 0.0)}")
        print(f"   net_debit={idea.get('net_debit', 0.0)}")
        print(f"   width={idea.get('width', 0.0)}")
        print(f"   max_risk={idea.get('max_risk', 0.0)}")
        print(f"   score={idea.get('score', 0.0)}")
        print(f"   market_regime={idea.get('market_regime', 'UNKNOWN')}")
        print(
            "   directional_state="
            f"{idea.get('directional_state', 'UNKNOWN')}"
        )
        print(f"   iv_state={idea.get('iv_state', 'UNKNOWN')}")

    return output_path


if __name__ == "__main__":
    run_trade_ideas()
