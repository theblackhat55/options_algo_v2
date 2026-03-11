from __future__ import annotations

from options_algo_v2.domain.trade_candidate import TradeCandidate


def _serialize_leg(leg: object) -> dict[str, object]:
    bid = float(getattr(leg, "bid", 0.0) or 0.0)
    ask = float(getattr(leg, "ask", 0.0) or 0.0)
    mid = float(getattr(leg, "mid", 0.0) or 0.0)

    return {
        "option_symbol": str(getattr(leg, "option_symbol", "")),
        "expiration": str(getattr(leg, "expiration", "")),
        "strike": float(getattr(leg, "strike", 0.0) or 0.0),
        "option_type": str(getattr(leg, "option_type", "")),
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "delta": getattr(leg, "delta", None),
        "implied_volatility": getattr(leg, "implied_volatility", None),
        "open_interest": int(getattr(leg, "open_interest", 0) or 0),
        "volume": int(getattr(leg, "volume", 0) or 0),
        "is_invalid_quote": bid <= 0.0 or ask <= 0.0 or ask < bid,
        "is_locked_quote": bid > 0.0 and ask > 0.0 and ask == bid,
        "spread_width": max(0.0, ask - bid),
    }


def build_trade_candidate_spread_debug(candidate: TradeCandidate) -> dict[str, object]:
    short_leg = candidate.short_leg
    long_leg = candidate.long_leg

    short_leg_payload = _serialize_leg(short_leg)
    long_leg_payload = _serialize_leg(long_leg)

    return {
        "symbol": candidate.symbol,
        "strategy_family": candidate.strategy_family,
        "short_leg": short_leg_payload,
        "long_leg": long_leg_payload,
        "width": float(candidate.width),
        "net_credit": float(candidate.net_credit),
        "net_debit": float(candidate.net_debit),
        "has_positive_width": float(candidate.width) > 0.0,
        "has_nonnegative_pricing": (
            float(candidate.net_credit) >= 0.0 and float(candidate.net_debit) >= 0.0
        ),
        "short_leg_invalid_quote": bool(short_leg_payload["is_invalid_quote"]),
        "long_leg_invalid_quote": bool(long_leg_payload["is_invalid_quote"]),
        "short_leg_locked_quote": bool(short_leg_payload["is_locked_quote"]),
        "long_leg_locked_quote": bool(long_leg_payload["is_locked_quote"]),
    }
