from __future__ import annotations

from options_algo_v2.domain.qualification import QualificationResult


def passes_liquidity_filter(
    *,
    underlying_price: float,
    avg_daily_volume: float,
    option_open_interest: int,
    option_volume: int,
    bid: float,
    ask: float,
    option_quote_age_seconds: int,
    underlying_quote_age_seconds: int,
    min_underlying_price: float,
    min_avg_daily_volume: float,
    min_option_open_interest: int,
    min_option_volume: int,
    max_bid_ask_spread_pct: float,
    max_option_quote_age_seconds: int,
    max_underlying_quote_age_seconds: int,
) -> QualificationResult:
    reasons: list[str] = []

    if underlying_price < min_underlying_price:
        reasons.append("underlying price below minimum")

    if avg_daily_volume < min_avg_daily_volume:
        reasons.append("underlying average daily volume below minimum")

    if option_open_interest < min_option_open_interest:
        reasons.append("option open interest below minimum")

    if option_volume < min_option_volume:
        reasons.append("option volume below minimum")

    if bid <= 0 or ask <= 0 or ask <= bid:
        reasons.append("invalid bid ask quote")
    else:
        mid = (bid + ask) / 2.0
        spread_pct = (ask - bid) / mid
        if spread_pct > max_bid_ask_spread_pct:
            reasons.append("bid ask spread exceeds maximum percentage")

    if option_quote_age_seconds > max_option_quote_age_seconds:
        reasons.append("option quote too stale")

    if underlying_quote_age_seconds > max_underlying_quote_age_seconds:
        reasons.append("underlying quote too stale")

    return QualificationResult(
        passed=len(reasons) == 0,
        reasons=reasons,
    )
