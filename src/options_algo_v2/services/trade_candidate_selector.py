from __future__ import annotations

from typing import TypedDict

from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.spread_scoring import (
    SpreadScoreBreakdown,
    score_bull_call_spread,
    score_bull_put_spread,
)
from options_algo_v2.services.spread_selection_filters import (
    passes_bull_call_delta_filter,
    passes_bull_put_delta_filter,
    passes_credit_width_filter,
    passes_debit_width_filter,
)


class RankedTradeCandidate(TypedDict):
    symbol: str
    strategy_family: str
    expiration: str
    net_credit: float
    net_debit: float
    width: float
    score: float
    score_breakdown: dict[str, float]


def _breakdown_to_dict(breakdown: SpreadScoreBreakdown) -> dict[str, float]:
    return {
        "delta_fit": breakdown["delta_fit"],
        "liquidity": breakdown["liquidity"],
        "efficiency": breakdown["efficiency"],
        "total": breakdown["total"],
    }


def select_and_rank_trade_candidates(
    candidates: list[TradeCandidate],
) -> list[RankedTradeCandidate]:
    ranked: list[RankedTradeCandidate] = []

    for candidate in candidates:
        if candidate.strategy_family in {"BULL_PUT_SPREAD", "BEAR_CALL_SPREAD"}:
            if not passes_bull_put_delta_filter(candidate):
                continue
            if not passes_credit_width_filter(candidate):
                continue
            short_leg_delta = candidate.short_leg.delta
            if short_leg_delta is None:
                continue

            breakdown = score_bull_put_spread(
                short_leg_delta=short_leg_delta,
                short_leg_open_interest=candidate.short_leg.open_interest,
                net_credit=candidate.net_credit,
                width=candidate.width,
            )
        elif candidate.strategy_family in {"BULL_CALL_SPREAD", "BEAR_PUT_SPREAD"}:
            if not passes_bull_call_delta_filter(candidate):
                continue
            if not passes_debit_width_filter(candidate):
                continue
            long_leg_delta = candidate.long_leg.delta
            if long_leg_delta is None:
                continue

            breakdown = score_bull_call_spread(
                long_leg_delta=long_leg_delta,
                long_leg_open_interest=candidate.long_leg.open_interest,
                net_debit=candidate.net_debit,
                width=candidate.width,
            )
        else:
            continue

        ranked.append(
            {
                "symbol": candidate.symbol,
                "strategy_family": candidate.strategy_family,
                "expiration": candidate.expiration,
                "net_credit": candidate.net_credit,
                "net_debit": candidate.net_debit,
                "width": candidate.width,
                "score": breakdown["total"],
                "score_breakdown": _breakdown_to_dict(breakdown),
            }
        )

    return sorted(ranked, key=lambda item: item["score"], reverse=True)
