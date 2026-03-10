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
) -> QualificationResult:
    reasons: list[str] = []

    if underlying_price < 20.0:
        reasons.append("underlying price below minimum")

    if avg_daily_volume < 1_000_000:
        reasons.append("underlying average daily volume below minimum")

    if option_open_interest < 500:
        reasons.append("option open interest below minimum")

    if option_volume < 100:
        reasons.append("option volume below minimum")

    if bid <= 0 or ask <= 0 or ask <= bid:
        reasons.append("invalid bid ask quote")
    else:
        mid = (bid + ask) / 2.0
        spread_pct = (ask - bid) / mid
        if spread_pct > 0.08:
            reasons.append("bid ask spread exceeds maximum percentage")

    if option_quote_age_seconds > 60:
        reasons.append("option quote too stale")

    if underlying_quote_age_seconds > 10:
        reasons.append("underlying quote too stale")

    return QualificationResult(
        passed=len(reasons) == 0,
        reasons=reasons,
    )
