from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OptionsWatchlistRow:
    symbol: str
    watchlist_score: float
    options_viability_score: float
    combined_score: float
    options_viable: bool
    expiration_count: int
    contract_count: int
    call_count: int
    put_count: int
    total_option_volume: int
    total_open_interest: int
    nonzero_bid_ask_count: int
    nonzero_open_interest_count: int
    nonzero_delta_count: int
    reason_codes: list[str]


def _to_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return float(stripped)
        except ValueError:
            return default
    return default


def _to_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return default
        try:
            return int(float(stripped))
        except ValueError:
            return default
    return default


def _is_call(option_type: object) -> bool:
    if not isinstance(option_type, str):
        return False
    return option_type.strip().upper() == "CALL"


def _is_put(option_type: object) -> bool:
    if not isinstance(option_type, str):
        return False
    return option_type.strip().upper() == "PUT"


def build_options_watchlist_row(
    *,
    base_row: dict[str, object],
    quotes: list[object],
) -> OptionsWatchlistRow:
    symbol = str(base_row["symbol"])
    watchlist_score = _to_float(base_row.get("watchlist_score"), 0.0)

    expirations: set[str] = set()
    contract_count = 0
    call_count = 0
    put_count = 0
    total_option_volume = 0
    total_open_interest = 0
    nonzero_bid_ask_count = 0
    nonzero_open_interest_count = 0
    nonzero_delta_count = 0

    for quote in quotes:
        contract_count += 1

        expiration = getattr(quote, "expiration", None)
        if isinstance(expiration, str) and expiration.strip():
            expirations.add(expiration.strip())

        option_type = getattr(quote, "option_type", None)
        if _is_call(option_type):
            call_count += 1
        elif _is_put(option_type):
            put_count += 1

        bid = _to_float(getattr(quote, "bid", 0.0), 0.0)
        ask = _to_float(getattr(quote, "ask", 0.0), 0.0)
        volume = _to_int(getattr(quote, "volume", 0), 0)
        open_interest = _to_int(getattr(quote, "open_interest", 0), 0)
        delta = _to_float(getattr(quote, "delta", 0.0), 0.0)

        total_option_volume += volume
        total_open_interest += open_interest

        if bid > 0 and ask > 0:
            nonzero_bid_ask_count += 1
        if open_interest > 0:
            nonzero_open_interest_count += 1
        if abs(delta) > 0:
            nonzero_delta_count += 1

    expiration_count = len(expirations)

    contract_score = min(contract_count / 200.0, 1.0) * 20.0
    expiration_score = min(expiration_count / 6.0, 1.0) * 15.0
    volume_score = min(total_option_volume / 5000.0, 1.0) * 20.0
    oi_score = min(total_open_interest / 20000.0, 1.0) * 20.0
    quote_score = min(nonzero_bid_ask_count / max(contract_count, 1), 1.0) * 15.0
    delta_score = min(nonzero_delta_count / max(contract_count, 1), 1.0) * 10.0

    options_viability_score = round(
        contract_score
        + expiration_score
        + volume_score
        + oi_score
        + quote_score
        + delta_score,
        3,
    )

    combined_score = round(
        (watchlist_score * 0.6) + (options_viability_score * 0.4),
        3,
    )

    reason_codes: list[str] = []
    if contract_count == 0:
        reason_codes.append("no_contracts")
    if expiration_count == 0:
        reason_codes.append("no_expirations")
    if total_option_volume <= 0:
        reason_codes.append("zero_option_volume")
    if total_open_interest <= 0:
        reason_codes.append("zero_open_interest")
    if nonzero_bid_ask_count == 0:
        reason_codes.append("no_nonzero_bid_ask_quotes")
    if nonzero_delta_count == 0:
        reason_codes.append("no_nonzero_delta_quotes")

    options_viable = (
        contract_count >= 20
        and expiration_count >= 1
        and nonzero_bid_ask_count >= 5
    )

    return OptionsWatchlistRow(
        symbol=symbol,
        watchlist_score=watchlist_score,
        options_viability_score=options_viability_score,
        combined_score=combined_score,
        options_viable=options_viable,
        expiration_count=expiration_count,
        contract_count=contract_count,
        call_count=call_count,
        put_count=put_count,
        total_option_volume=total_option_volume,
        total_open_interest=total_open_interest,
        nonzero_bid_ask_count=nonzero_bid_ask_count,
        nonzero_open_interest_count=nonzero_open_interest_count,
        nonzero_delta_count=nonzero_delta_count,
        reason_codes=reason_codes,
    )


def sort_options_watchlist_rows(
    rows: list[OptionsWatchlistRow],
) -> list[OptionsWatchlistRow]:
    return sorted(rows, key=lambda row: row.combined_score, reverse=True)
