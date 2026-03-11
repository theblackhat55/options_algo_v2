from __future__ import annotations

from collections.abc import Sequence
from math import log, sqrt
from statistics import mean, pstdev

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot

TRADING_DAYS_PER_YEAR = 252.0


def _to_float(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def compute_hv20_from_bar_rows(bar_rows: Sequence[dict[str, object]]) -> float | None:
    closes: list[float] = []

    for row in bar_rows:
        close = _to_float(row.get("close"))
        if close is not None and close > 0:
            closes.append(close)

    if len(closes) < 21:
        return None

    log_returns: list[float] = []
    for previous, current in zip(closes[:-1], closes[1:], strict=False):
        if previous <= 0 or current <= 0:
            continue
        log_returns.append(log(current / previous))

    if len(log_returns) < 20:
        return None

    stdev = pstdev(log_returns[-20:])
    return stdev * sqrt(TRADING_DAYS_PER_YEAR)


def _quote_has_liquidity(quote: OptionQuote) -> bool:
    bid = _to_float(quote.bid)
    ask = _to_float(quote.ask)
    mid = _to_float(quote.mid)
    open_interest = _to_float(quote.open_interest)
    volume = _to_float(quote.volume)

    if bid is None or ask is None or mid is None:
        return False
    if bid < 0 or ask <= 0 or ask < bid or mid <= 0:
        return False
    if (
        open_interest is not None
        and open_interest <= 0
        and volume is not None
        and volume <= 0
    ):
        return False
    return True


def _extract_implied_vol(quote: OptionQuote) -> float | None:
    implied_vol = _to_float(getattr(quote, "implied_volatility", None))
    if implied_vol is None or implied_vol <= 0:
        return None
    if implied_vol > 3.0:
        return implied_vol / 100.0
    return implied_vol


def estimate_near_atm_implied_vol(
    snapshot: OptionsChainSnapshot,
    underlying_price: float,
) -> float | None:
    candidates: list[tuple[float, float]] = []

    for quote in snapshot.quotes:
        strike = _to_float(getattr(quote, "strike", None))
        if strike is None or strike <= 0:
            continue

        if not _quote_has_liquidity(quote):
            continue

        implied_vol = _extract_implied_vol(quote)
        if implied_vol is None or implied_vol <= 0:
            continue

        distance = abs(strike - underlying_price)
        candidates.append((distance, implied_vol))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    nearest = [iv for _, iv in candidates[:4]]
    if not nearest:
        return None

    return mean(nearest)


def compute_iv_hv_ratio_from_snapshot_and_bars(
    snapshot: OptionsChainSnapshot,
    bar_rows: Sequence[dict[str, object]],
    underlying_price: float,
) -> float | None:
    implied_vol = estimate_near_atm_implied_vol(
        snapshot=snapshot,
        underlying_price=underlying_price,
    )
    historical_vol = compute_hv20_from_bar_rows(bar_rows)

    if implied_vol is None or historical_vol is None or historical_vol <= 0:
        return None

    return implied_vol / historical_vol
