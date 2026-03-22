from __future__ import annotations

from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.history_store import load_underlying_bars
from options_algo_v2.services.support_resistance import (
    identify_support_resistance,
    validate_strike_near_support_resistance,
)


def _build_support_resistance_payload(candidate: TradeCandidate) -> dict[str, object]:
    strategy_family = candidate.strategy_family
    if strategy_family not in {"BULL_PUT_SPREAD", "BEAR_CALL_SPREAD"}:
        return {}

    try:
        bars = load_underlying_bars(
            symbol=candidate.symbol,
            start_date=None,
            end_date=None,
        )
    except Exception:
        return {}

    closes = [float(bar.close) for bar in bars if getattr(bar, "close", None) is not None]
    if len(closes) < 20:
        return {}

    levels = identify_support_resistance(closes, lookback=20, tolerance_pct=0.5)

    if strategy_family == "BULL_PUT_SPREAD":
        kind = "support"
        strike = float(candidate.short_leg.strike)
    else:
        kind = "resistance"
        strike = float(candidate.short_leg.strike)

    is_valid, distance_pct = validate_strike_near_support_resistance(
        strike=strike,
        levels=levels,
        kind=kind,
        max_distance_pct=2.0,
    )

    return {
        "support_resistance_valid": bool(is_valid),
        "support_resistance_kind": kind,
        "support_resistance_distance_pct": float(distance_pct),
    }


def serialize_trade_candidate(candidate: TradeCandidate) -> dict[str, object]:
    payload = {
        "symbol": candidate.symbol,
        "strategy_family": candidate.strategy_family,
        "expiration": candidate.expiration,
        "short_leg": {
            "option_symbol": candidate.short_leg.option_symbol,
            "strike": candidate.short_leg.strike,
            "option_type": candidate.short_leg.option_type,
            "bid": candidate.short_leg.bid,
            "ask": candidate.short_leg.ask,
            "mid": candidate.short_leg.mid,
            "delta": candidate.short_leg.delta,
            "open_interest": candidate.short_leg.open_interest,
            "volume": candidate.short_leg.volume,
        },
        "long_leg": {
            "option_symbol": candidate.long_leg.option_symbol,
            "strike": candidate.long_leg.strike,
            "option_type": candidate.long_leg.option_type,
            "bid": candidate.long_leg.bid,
            "ask": candidate.long_leg.ask,
            "mid": candidate.long_leg.mid,
            "delta": candidate.long_leg.delta,
            "open_interest": candidate.long_leg.open_interest,
            "volume": candidate.long_leg.volume,
        },
        "net_debit": candidate.net_debit,
        "net_credit": candidate.net_credit,
        "width": candidate.width,
    }
    payload.update(_build_support_resistance_payload(candidate))
    return payload
