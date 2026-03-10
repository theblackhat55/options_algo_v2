from __future__ import annotations

from options_algo_v2.domain.trade_candidate import TradeCandidate


def serialize_trade_candidate(candidate: TradeCandidate) -> dict[str, object]:
    return {
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
