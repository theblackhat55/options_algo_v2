from __future__ import annotations

from typing import TypedDict


class SpreadScoreBreakdown(TypedDict):
    delta_fit: float
    liquidity: float
    efficiency: float
    total: float


def _closeness_score(value: float, target: float, tolerance: float) -> float:
    distance = abs(value - target)
    if tolerance <= 0:
        return 0.0
    return max(0.0, 1.0 - (distance / tolerance))


def score_bull_call_spread(
    *,
    long_leg_delta: float,
    long_leg_open_interest: int,
    net_debit: float,
    width: float,
) -> SpreadScoreBreakdown:
    delta_fit = _closeness_score(long_leg_delta, target=0.35, tolerance=0.20)
    liquidity = min(1.0, long_leg_open_interest / 2000.0)
    efficiency = 0.0 if width <= 0 else max(0.0, 1.0 - (net_debit / width))

    total = (0.45 * delta_fit) + (0.25 * liquidity) + (0.30 * efficiency)
    return {
        "delta_fit": round(delta_fit, 4),
        "liquidity": round(liquidity, 4),
        "efficiency": round(efficiency, 4),
        "total": round(total, 4),
    }


def score_bull_put_spread(
    *,
    short_leg_delta: float,
    short_leg_open_interest: int,
    net_credit: float,
    width: float,
) -> SpreadScoreBreakdown:
    abs_delta = abs(short_leg_delta)
    delta_fit = _closeness_score(abs_delta, target=0.28, tolerance=0.18)
    liquidity = min(1.0, short_leg_open_interest / 2000.0)
    efficiency = 0.0 if width <= 0 else min(1.0, net_credit / width)

    total = (0.45 * delta_fit) + (0.25 * liquidity) + (0.30 * efficiency)
    return {
        "delta_fit": round(delta_fit, 4),
        "liquidity": round(liquidity, 4),
        "efficiency": round(efficiency, 4),
        "total": round(total, 4),
    }
