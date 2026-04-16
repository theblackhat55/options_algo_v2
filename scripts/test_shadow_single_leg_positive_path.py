from __future__ import annotations

from datetime import date
from pprint import pprint
from types import SimpleNamespace

from options_algo_v2.domain.enums import StrategyType
from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.single_leg_shadow_mode import (
    build_shadow_single_leg_candidates,
    build_shadow_single_leg_debug,
)


def main() -> int:
    decision = SimpleNamespace(
        qualified=True,
        strategy_type=StrategyType.BULL_CALL_SPREAD,
        rationale=[
            "market_regime=TREND_UP",
            "directional_state=BULLISH_BREAKOUT",
            "iv_state=IV_NORMAL",
            "selected_strategy=BULL_CALL_SPREAD",
            "eligible_strategies=BULL_CALL_SPREAD,LONG_CALL",
            "long_call_alternative_eligible",
        ],
        candidate=SimpleNamespace(
            symbol="NFLX",
            strategy_type=StrategyType.BULL_CALL_SPREAD,
        ),
        symbol="NFLX",
    )

    options_chain = OptionsChainSnapshot(
        symbol="NFLX",
        as_of="2026-04-16T19:00:00Z",
        source="test_harness",
        quotes=[
            OptionQuote(
                symbol="NFLX",
                option_symbol="NFLX260515C00960000",
                expiration="2026-05-15",
                strike=960.0,
                option_type="CALL",
                bid=3.0,
                ask=3.2,
                mid=3.1,
                delta=0.52,
                implied_volatility=0.31,
                open_interest=1200,
                volume=150,
            ),
            OptionQuote(
                symbol="NFLX",
                option_symbol="NFLX260515C00970000",
                expiration="2026-05-15",
                strike=970.0,
                option_type="CALL",
                bid=2.4,
                ask=2.6,
                mid=2.5,
                delta=0.46,
                implied_volatility=0.30,
                open_interest=900,
                volume=120,
            ),
            OptionQuote(
                symbol="NFLX",
                option_symbol="NFLX260515P00940000",
                expiration="2026-05-15",
                strike=940.0,
                option_type="PUT",
                bid=2.8,
                ask=3.0,
                mid=2.9,
                delta=-0.41,
                implied_volatility=0.29,
                open_interest=700,
                volume=80,
            ),
        ],
    )

    debug = build_shadow_single_leg_debug(
        decision=decision,
        options_chain=options_chain,
    )
    candidates = build_shadow_single_leg_candidates(
        decision=decision,
        options_chain=options_chain,
        as_of_date=date(2026, 4, 16),
        limit=1,
    )

    if debug.get("qualified") and debug.get("has_options_chain") and debug.get("long_call_eligible"):
        debug["shadow_attempted"] = True
        debug["shadow_candidate_count"] = len(candidates)
        debug["reason"] = "candidates_found" if candidates else "selector_returned_no_candidates"

    print("shadow debug:")
    pprint(debug)
    print("\nshadow candidates:")
    pprint(candidates)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
