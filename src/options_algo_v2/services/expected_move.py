from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedMoveComparison:
    implied_move_pct: float
    forecast_move_pct: float
    ratio: float  # implied / forecast  (> 1 = premium overpriced, good for selling)
    edge: str  # "sell_premium" | "buy_premium" | "neutral"


def compute_implied_expected_move(
    *,
    atm_iv: float,
    dte_days: int,
) -> float:
    """Compute the implied expected move as a percentage of underlying price.

    Uses the standard approximation: expected_move_pct = atm_iv * sqrt(dte/365) * 100.
    Returns a value in percentage units (e.g. 8.5 means 8.5%).
    """
    if atm_iv <= 0 or dte_days <= 0:
        return 0.0
    return atm_iv * math.sqrt(dte_days / 365.0) * 100.0


def compute_forecast_move(
    *,
    atr20: float,
    close: float,
    dte_days: int,
) -> float:
    """Estimate the realized move as a percentage using ATR scaling.

    Annualized ATR-based volatility scaled to the DTE window.
    """
    if close <= 0 or atr20 <= 0 or dte_days <= 0:
        return 0.0
    daily_vol_pct = (atr20 / close) * 100.0
    return daily_vol_pct * math.sqrt(dte_days)


def compare_expected_moves(
    *,
    atm_iv: float,
    dte_days: int,
    atr20: float,
    close: float,
    sell_threshold: float = 1.15,
    buy_threshold: float = 0.85,
) -> ExpectedMoveComparison:
    """Compare implied vs forecast expected move.

    If the implied move is significantly larger than the forecast
    (ratio > sell_threshold), premium is overpriced — favor selling
    strategies (credit spreads). If implied is much smaller
    (ratio < buy_threshold), favor buying strategies (debit spreads).
    """
    implied_pct = compute_implied_expected_move(atm_iv=atm_iv, dte_days=dte_days)
    forecast_pct = compute_forecast_move(atr20=atr20, close=close, dte_days=dte_days)

    if forecast_pct <= 0 or implied_pct <= 0:
        return ExpectedMoveComparison(
            implied_move_pct=implied_pct,
            forecast_move_pct=forecast_pct,
            ratio=1.0,
            edge="neutral",
        )

    ratio = implied_pct / forecast_pct

    if ratio >= sell_threshold:
        edge = "sell_premium"
    elif ratio <= buy_threshold:
        edge = "buy_premium"
    else:
        edge = "neutral"

    return ExpectedMoveComparison(
        implied_move_pct=round(implied_pct, 4),
        forecast_move_pct=round(forecast_pct, 4),
        ratio=round(ratio, 4),
        edge=edge,
    )
