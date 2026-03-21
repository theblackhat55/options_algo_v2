from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime, date
from math import inf
from typing import Iterable

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.models.options_context import (
    ExpectedMoveSnapshot,
    OptionsContextSnapshot,
    PositioningSnapshot,
    SkewSnapshot,
)


def compute_expected_moves(
    *,
    spot_price: float | None,
    chain: OptionsChainSnapshot,
) -> ExpectedMoveSnapshot:
    if spot_price is None or spot_price <= 0:
        return ExpectedMoveSnapshot()

    return ExpectedMoveSnapshot(
        expected_move_1d_pct=_compute_expected_move_for_target_dte(
            spot_price=spot_price,
            chain=chain,
            target_dte=1,
        ),
        expected_move_1w_pct=_compute_expected_move_for_target_dte(
            spot_price=spot_price,
            chain=chain,
            target_dte=7,
        ),
        expected_move_30d_pct=_compute_expected_move_for_target_dte(
            spot_price=spot_price,
            chain=chain,
            target_dte=30,
        ),
    )


def compute_positioning_metrics(
    *,
    chain: OptionsChainSnapshot,
) -> PositioningSnapshot:
    call_quotes = [quote for quote in chain.quotes if quote.option_type == "CALL"]
    put_quotes = [quote for quote in chain.quotes if quote.option_type == "PUT"]

    call_oi_total = sum(max(int(quote.open_interest), 0) for quote in call_quotes)
    put_oi_total = sum(max(int(quote.open_interest), 0) for quote in put_quotes)
    call_volume_total = sum(max(int(quote.volume), 0) for quote in call_quotes)
    put_volume_total = sum(max(int(quote.volume), 0) for quote in put_quotes)

    pcr_oi = None
    if call_oi_total > 0:
        pcr_oi = put_oi_total / call_oi_total

    pcr_volume = None
    if call_volume_total > 0:
        pcr_volume = put_volume_total / call_volume_total

    return PositioningSnapshot(
        call_oi_total=call_oi_total,
        put_oi_total=put_oi_total,
        call_volume_total=call_volume_total,
        put_volume_total=put_volume_total,
        pcr_oi=pcr_oi,
        pcr_volume=pcr_volume,
    )


def compute_skew_metrics(
    *,
    spot_price: float | None,
    chain: OptionsChainSnapshot,
) -> SkewSnapshot:
    del spot_price  # reserved for future refinements

    target_expiry_quotes = _select_quotes_near_target_dte(chain.quotes, target_dte=30)
    if not target_expiry_quotes:
        return SkewSnapshot()

    put_quote = _select_quote_by_target_delta(
        quotes=target_expiry_quotes,
        option_type="PUT",
        target_delta=-0.25,
    )
    call_quote = _select_quote_by_target_delta(
        quotes=target_expiry_quotes,
        option_type="CALL",
        target_delta=0.25,
    )

    if put_quote is None or call_quote is None:
        return SkewSnapshot()

    put_iv = put_quote.implied_volatility
    call_iv = call_quote.implied_volatility

    if put_iv is None or call_iv is None or put_iv <= 0 or call_iv <= 0:
        return SkewSnapshot()

    return SkewSnapshot(
        skew_25d_put_call_ratio=put_iv / call_iv,
        skew_25d_put_call_spread=put_iv - call_iv,
    )




def compute_chain_quality_metrics(
    *,
    chain: OptionsChainSnapshot,
) -> dict[str, int | float | None]:
    quotes = list(chain.quotes)
    contract_count = len(quotes)
    expiration_count = len({_parse_expiration_date(q.expiration) for q in quotes if _parse_expiration_date(q.expiration) is not None})

    if contract_count == 0:
        return {
            "contract_count": 0,
            "expiration_count": 0,
            "nonzero_bid_ask_ratio": None,
            "nonzero_open_interest_ratio": None,
            "nonzero_delta_ratio": None,
            "nonzero_iv_ratio": None,
        }

    valid_bid_ask = sum(
        1
        for q in quotes
        if q.bid > 0 and q.ask > 0 and q.ask >= q.bid
    )
    valid_open_interest = sum(1 for q in quotes if int(q.open_interest or 0) > 0)
    valid_delta = sum(1 for q in quotes if q.delta is not None)
    valid_iv = sum(
        1
        for q in quotes
        if q.implied_volatility is not None and q.implied_volatility > 0
    )

    return {
        "contract_count": contract_count,
        "expiration_count": expiration_count,
        "nonzero_bid_ask_ratio": valid_bid_ask / contract_count,
        "nonzero_open_interest_ratio": valid_open_interest / contract_count,
        "nonzero_delta_ratio": valid_delta / contract_count,
        "nonzero_iv_ratio": valid_iv / contract_count,
    }


def compute_atm_iv(
    *,
    spot_price: float | None,
    chain: OptionsChainSnapshot,
) -> float | None:
    if spot_price is None or spot_price <= 0:
        return None

    quotes = _select_quotes_near_target_dte(chain.quotes, target_dte=30)
    if not quotes:
        quotes = list(chain.quotes)

    call_quote = _select_nearest_atm_quote(
        quotes=quotes,
        option_type="CALL",
        spot_price=spot_price,
    )
    put_quote = _select_nearest_atm_quote(
        quotes=quotes,
        option_type="PUT",
        spot_price=spot_price,
    )

    ivs = [
        q.implied_volatility
        for q in (call_quote, put_quote)
        if q is not None and q.implied_volatility is not None and q.implied_volatility > 0
    ]
    if not ivs:
        return None
    return sum(ivs) / len(ivs)


def classify_options_summary_regime(
    *,
    confidence_score: float,
    nonzero_bid_ask_ratio: float | None,
    nonzero_open_interest_ratio: float | None,
    pcr_oi: float | None,
) -> str:
    bid_ask = nonzero_bid_ask_ratio if nonzero_bid_ask_ratio is not None else 0.0
    oi_ratio = (
        nonzero_open_interest_ratio if nonzero_open_interest_ratio is not None else 0.0
    )

    if confidence_score < 0.50 and bid_ask < 0.50:
        return "illiquid"
    if bid_ask < 0.65 or oi_ratio < 0.50:
        return "limited"
    if pcr_oi is not None and pcr_oi >= 1.25:
        return "put_heavy_liquid"
    if pcr_oi is not None and pcr_oi <= 0.75:
        return "call_heavy_liquid"
    return "tradable"
def compute_options_context_snapshot(
    *,
    symbol: str,
    as_of_utc: str | None,
    spot_price: float | None,
    chain: OptionsChainSnapshot,
    source_provider: str,
) -> OptionsContextSnapshot:
    expected_move = compute_expected_moves(spot_price=spot_price, chain=chain)
    positioning = compute_positioning_metrics(chain=chain)
    skew = compute_skew_metrics(spot_price=spot_price, chain=chain)
    quality = compute_chain_quality_metrics(chain=chain)
    atm_iv = compute_atm_iv(spot_price=spot_price, chain=chain)

    confidence_score, confidence_reasons, missing_fields = _compute_confidence(
        spot_price=spot_price,
        chain=chain,
        expected_move=expected_move,
        positioning=positioning,
        skew=skew,
    )

    options_summary_regime = classify_options_summary_regime(
        confidence_score=confidence_score,
        nonzero_bid_ask_ratio=quality.get("nonzero_bid_ask_ratio"),
        nonzero_open_interest_ratio=quality.get("nonzero_open_interest_ratio"),
        pcr_oi=positioning.pcr_oi,
    )

    return OptionsContextSnapshot(
        symbol=symbol,
        as_of_utc=as_of_utc or _utc_now_iso(),
        spot_price=spot_price,
        source_provider=source_provider,
        confidence_score=confidence_score,
        confidence_reasons=confidence_reasons,
        missing_fields=missing_fields,
        contract_count=quality.get("contract_count"),
        expiration_count=quality.get("expiration_count"),
        atm_iv=atm_iv,
        nonzero_bid_ask_ratio=quality.get("nonzero_bid_ask_ratio"),
        nonzero_open_interest_ratio=quality.get("nonzero_open_interest_ratio"),
        nonzero_delta_ratio=quality.get("nonzero_delta_ratio"),
        nonzero_iv_ratio=quality.get("nonzero_iv_ratio"),
        options_summary_regime=options_summary_regime,
        **asdict(expected_move),
        **asdict(positioning),
        **asdict(skew),
    )


def _compute_expected_move_for_target_dte(
    *,
    spot_price: float,
    chain: OptionsChainSnapshot,
    target_dte: int,
) -> float | None:
    quotes = _select_quotes_near_target_dte(chain.quotes, target_dte=target_dte)
    if not quotes:
        return None

    call_quote = _select_nearest_atm_quote(
        quotes=quotes,
        option_type="CALL",
        spot_price=spot_price,
    )
    put_quote = _select_nearest_atm_quote(
        quotes=quotes,
        option_type="PUT",
        spot_price=spot_price,
    )

    if call_quote is None or put_quote is None:
        return None

    if call_quote.mid <= 0 or put_quote.mid <= 0:
        return None

    return (call_quote.mid + put_quote.mid) / spot_price


def _select_quotes_near_target_dte(
    quotes: Iterable[OptionQuote],
    *,
    target_dte: int,
) -> list[OptionQuote]:
    grouped = _group_quotes_by_expiry(quotes)
    if not grouped:
        return []

    today = datetime.now(UTC).date()
    best_expiry: date | None = None
    best_distance: int | float = inf

    for expiry_date in grouped:
        dte = (expiry_date - today).days
        if dte < 0:
            continue
        distance = abs(dte - target_dte)
        if distance < best_distance:
            best_distance = distance
            best_expiry = expiry_date

    if best_expiry is None:
        return []

    return grouped[best_expiry]


def _group_quotes_by_expiry(
    quotes: Iterable[OptionQuote],
) -> dict[date, list[OptionQuote]]:
    grouped: dict[date, list[OptionQuote]] = {}
    for quote in quotes:
        expiry = _parse_expiration_date(quote.expiration)
        if expiry is None:
            continue
        grouped.setdefault(expiry, []).append(quote)
    return grouped


def _select_nearest_atm_quote(
    *,
    quotes: Iterable[OptionQuote],
    option_type: str,
    spot_price: float,
) -> OptionQuote | None:
    filtered = [
        quote
        for quote in quotes
        if quote.option_type == option_type and quote.mid > 0
    ]
    if not filtered:
        return None

    return min(
        filtered,
        key=lambda quote: (abs(quote.strike - spot_price), -quote.volume, -quote.open_interest),
    )


def _select_quote_by_target_delta(
    *,
    quotes: Iterable[OptionQuote],
    option_type: str,
    target_delta: float,
) -> OptionQuote | None:
    filtered = [
        quote
        for quote in quotes
        if quote.option_type == option_type
        and quote.delta is not None
        and quote.implied_volatility is not None
        and quote.implied_volatility > 0
    ]
    if not filtered:
        return None

    return min(
        filtered,
        key=lambda quote: (
            abs((quote.delta or 0.0) - target_delta),
            -quote.volume,
            -quote.open_interest,
        ),
    )


def _compute_confidence(
    *,
    spot_price: float | None,
    chain: OptionsChainSnapshot,
    expected_move: ExpectedMoveSnapshot,
    positioning: PositioningSnapshot,
    skew: SkewSnapshot,
) -> tuple[float, list[str], list[str]]:
    score = 1.0
    reasons: list[str] = []
    missing_fields: list[str] = []

    if spot_price is None or spot_price <= 0:
        score -= 0.40
        reasons.append("missing_or_invalid_spot_price")
        missing_fields.extend(
            [
                "expected_move_1d_pct",
                "expected_move_1w_pct",
                "expected_move_30d_pct",
                "skew_25d_put_call_ratio",
                "skew_25d_put_call_spread",
            ]
        )

    if len(chain.quotes) < 10:
        score -= 0.15
        reasons.append("sparse_options_chain")

    quotes_with_iv = [quote for quote in chain.quotes if quote.implied_volatility is not None]
    if len(quotes_with_iv) < 5:
        score -= 0.10
        reasons.append("limited_iv_coverage")

    quotes_with_delta = [quote for quote in chain.quotes if quote.delta is not None]
    if len(quotes_with_delta) < 5:
        score -= 0.10
        reasons.append("limited_delta_coverage")

    if expected_move.expected_move_1d_pct is None:
        score -= 0.10
        reasons.append("missing_expected_move_1d")
        missing_fields.append("expected_move_1d_pct")

    if expected_move.expected_move_1w_pct is None:
        score -= 0.10
        reasons.append("missing_expected_move_1w")
        missing_fields.append("expected_move_1w_pct")

    if expected_move.expected_move_30d_pct is None:
        score -= 0.10
        reasons.append("missing_expected_move_30d")
        missing_fields.append("expected_move_30d_pct")

    if positioning.pcr_oi is None:
        score -= 0.10
        reasons.append("missing_pcr_oi")
        missing_fields.append("pcr_oi")

    if positioning.pcr_volume is None:
        score -= 0.10
        reasons.append("missing_pcr_volume")
        missing_fields.append("pcr_volume")

    if skew.skew_25d_put_call_ratio is None:
        score -= 0.15
        reasons.append("missing_skew_ratio")
        missing_fields.append("skew_25d_put_call_ratio")

    if skew.skew_25d_put_call_spread is None:
        missing_fields.append("skew_25d_put_call_spread")

    score = max(0.0, min(1.0, score))
    return score, sorted(set(reasons)), sorted(set(missing_fields))


def _parse_expiration_date(value: str) -> date | None:
    text = value.strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
