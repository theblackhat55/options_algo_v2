from __future__ import annotations

from dataclasses import replace
from math import sqrt

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.models.options_context import OptionsContextRow


def _ratio(numerator: int | float | None, denominator: int | float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return float(numerator) / float(denominator)


def _count_valid_bid_ask(quotes: list[OptionQuote]) -> int:
    return sum(1 for q in quotes if q.bid > 0 and q.ask > 0)


def _count_valid_oi(quotes: list[OptionQuote]) -> int:
    return sum(1 for q in quotes if q.open_interest > 0)


def _count_valid_volume(quotes: list[OptionQuote]) -> int:
    return sum(1 for q in quotes if q.volume > 0)


def _count_valid_delta(quotes: list[OptionQuote]) -> int:
    return sum(1 for q in quotes if q.delta is not None and abs(q.delta) > 0)


def _count_valid_iv(quotes: list[OptionQuote]) -> int:
    return sum(1 for q in quotes if q.implied_volatility is not None and q.implied_volatility > 0)


def _select_atm_iv(quotes: list[OptionQuote]) -> float | None:
    candidates: list[tuple[float, float]] = []
    for q in quotes:
        if q.delta is None or q.implied_volatility is None or q.implied_volatility <= 0:
            continue
        candidates.append((abs(abs(q.delta) - 0.5), q.implied_volatility))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _select_25d_iv(quotes: list[OptionQuote], option_type: str) -> float | None:
    candidates: list[tuple[float, float]] = []
    for q in quotes:
        if q.option_type != option_type:
            continue
        if q.delta is None or q.implied_volatility is None or q.implied_volatility <= 0:
            continue
        candidates.append((abs(abs(q.delta) - 0.25), q.implied_volatility))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _compute_expected_moves_pct(atm_iv: float | None) -> tuple[float | None, float | None, float | None]:
    if atm_iv is None or atm_iv <= 0:
        return None, None, None
    return (
        atm_iv * sqrt(1 / 252) * 100,
        atm_iv * sqrt(5 / 252) * 100,
        atm_iv * sqrt(30 / 252) * 100,
    )


def _classify_summary_regime(
    *,
    contract_count: int,
    expiration_count: int,
    pcr_oi: float | None,
    nonzero_iv_ratio: float | None,
    nonzero_bid_ask_ratio: float | None,
) -> str:
    if contract_count < 20 or (nonzero_bid_ask_ratio or 0.0) < 0.25:
        return "thin"
    if (nonzero_iv_ratio or 0.0) < 0.20:
        return "iv_sparse"
    if expiration_count >= 3 and (nonzero_bid_ask_ratio or 0.0) >= 0.70:
        if pcr_oi is not None and pcr_oi > 1.20:
            return "put_heavy_liquid"
        if pcr_oi is not None and pcr_oi < 0.80:
            return "call_heavy_liquid"
        return "broad_liquid"
    return "tradable"


def _compute_confidence(row: OptionsContextRow) -> OptionsContextRow:
    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []

    def present(name: str, value, weight: float, reason: str) -> None:
        nonlocal score
        if value is None:
            missing.append(name)
        else:
            score += weight
            reasons.append(reason)

    present("contract_count", row.contract_count, 0.10, "contract_count_available")
    present("expiration_count", row.expiration_count, 0.10, "expiration_count_available")
    present("pcr_oi", row.pcr_oi, 0.15, "pcr_oi_available")
    present("pcr_volume", row.pcr_volume, 0.10, "pcr_volume_available")
    present("atm_iv", row.atm_iv, 0.15, "atm_iv_available")
    present("expected_move_1d_pct", row.expected_move_1d_pct, 0.10, "expected_move_available")
    present("skew_25d_put_call_ratio", row.skew_25d_put_call_ratio, 0.15, "skew_available")
    present("nonzero_bid_ask_ratio", row.nonzero_bid_ask_ratio, 0.05, "quote_quality_available")
    present("nonzero_delta_ratio", row.nonzero_delta_ratio, 0.05, "delta_coverage_available")
    present("nonzero_iv_ratio", row.nonzero_iv_ratio, 0.05, "iv_coverage_available")

    score = round(min(score, 1.0), 4)
    return replace(row, confidence_score=score, confidence_reasons=reasons, missing_fields=missing)


def compute_options_context_row_from_snapshot(snapshot: OptionsChainSnapshot) -> OptionsContextRow:
    quotes = list(snapshot.quotes)
    contract_count = len(quotes)
    expiration_count = len({q.expiration for q in quotes if q.expiration})

    calls = [q for q in quotes if q.option_type == "CALL"]
    puts = [q for q in quotes if q.option_type == "PUT"]

    call_count = len(calls)
    put_count = len(puts)

    call_oi_total = sum(q.open_interest for q in calls)
    put_oi_total = sum(q.open_interest for q in puts)
    call_volume_total = sum(q.volume for q in calls)
    put_volume_total = sum(q.volume for q in puts)

    pcr_oi = _ratio(put_oi_total, call_oi_total)
    pcr_volume = _ratio(put_volume_total, call_volume_total)

    atm_iv = _select_atm_iv(quotes)
    em1d, em1w, em30d = _compute_expected_moves_pct(atm_iv)

    put_25d_iv = _select_25d_iv(quotes, "PUT")
    call_25d_iv = _select_25d_iv(quotes, "CALL")

    skew_ratio = None
    skew_spread = None
    if put_25d_iv is not None and call_25d_iv is not None and call_25d_iv > 0:
        skew_ratio = put_25d_iv / call_25d_iv
        skew_spread = put_25d_iv - call_25d_iv

    nonzero_bid_ask_count = _count_valid_bid_ask(quotes)
    nonzero_open_interest_count = _count_valid_oi(quotes)
    nonzero_delta_count = _count_valid_delta(quotes)
    nonzero_iv_count = _count_valid_iv(quotes)

    nonzero_bid_ask_ratio = _ratio(nonzero_bid_ask_count, contract_count)
    nonzero_open_interest_ratio = _ratio(nonzero_open_interest_count, contract_count)
    nonzero_delta_ratio = _ratio(nonzero_delta_count, contract_count)
    nonzero_iv_ratio = _ratio(nonzero_iv_count, contract_count)

    regime = _classify_summary_regime(
        contract_count=contract_count,
        expiration_count=expiration_count,
        pcr_oi=pcr_oi,
        nonzero_iv_ratio=nonzero_iv_ratio,
        nonzero_bid_ask_ratio=nonzero_bid_ask_ratio,
    )

    row = OptionsContextRow(
        symbol=snapshot.symbol,
        as_of_utc=snapshot.as_of,
        source_provider=snapshot.source,
        contract_count=contract_count,
        expiration_count=expiration_count,
        call_count=call_count,
        put_count=put_count,
        call_oi_total=call_oi_total,
        put_oi_total=put_oi_total,
        call_volume_total=call_volume_total,
        put_volume_total=put_volume_total,
        pcr_oi=pcr_oi,
        pcr_volume=pcr_volume,
        atm_iv=atm_iv,
        expected_move_1d_pct=em1d,
        expected_move_1w_pct=em1w,
        expected_move_30d_pct=em30d,
        skew_25d_put_call_ratio=skew_ratio,
        skew_25d_put_call_spread=skew_spread,
        nonzero_bid_ask_count=nonzero_bid_ask_count,
        nonzero_open_interest_count=nonzero_open_interest_count,
        nonzero_delta_count=nonzero_delta_count,
        nonzero_iv_count=nonzero_iv_count,
        nonzero_bid_ask_ratio=nonzero_bid_ask_ratio,
        nonzero_open_interest_ratio=nonzero_open_interest_ratio,
        nonzero_delta_ratio=nonzero_delta_ratio,
        nonzero_iv_ratio=nonzero_iv_ratio,
        options_summary_regime=regime,
    )
    return _compute_confidence(row)
