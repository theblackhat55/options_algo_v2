from __future__ import annotations

from typing import Any


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value).strip()
        if not text:
            return None
        return float(text)
    except Exception:
        return None


def summarize_options_context_coverage(
    symbols: list[str],
    context_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    normalized = [s.strip().upper() for s in symbols if isinstance(s, str) and s.strip()]
    matched = [s for s in normalized if s in context_index]
    missing = [s for s in normalized if s not in context_index]

    regime_counts: dict[str, int] = {}
    low_confidence_symbols: list[str] = []
    expected_move_leaders: list[dict[str, Any]] = []
    skew_leaders: list[dict[str, Any]] = []

    for symbol in matched:
        row = context_index[symbol]
        regime = row.get("options_summary_regime") or "unknown"
        regime_counts[regime] = regime_counts.get(regime, 0) + 1

        confidence = _to_float(row.get("confidence_score")) or 0.0
        if confidence < 0.75:
            low_confidence_symbols.append(symbol)

        expected_move = _to_float(row.get("expected_move_1d_pct"))
        if expected_move is not None:
            expected_move_leaders.append(
                {"symbol": symbol, "expected_move_1d_pct": expected_move}
            )

        skew_ratio = _to_float(row.get("skew_25d_put_call_ratio"))
        if skew_ratio is not None:
            skew_leaders.append(
                {"symbol": symbol, "skew_25d_put_call_ratio": skew_ratio}
            )

    expected_move_leaders = sorted(
        expected_move_leaders,
        key=lambda item: item["expected_move_1d_pct"],
        reverse=True,
    )[:5]
    skew_leaders = sorted(
        skew_leaders,
        key=lambda item: item["skew_25d_put_call_ratio"],
        reverse=True,
    )[:5]

    return {
        "options_context_symbol_count": len(normalized),
        "options_context_matched_count": len(matched),
        "options_context_missing_count": len(missing),
        "options_context_missing_symbols": missing[:20],
        "options_context_regime_counts": regime_counts,
        "options_context_low_confidence_symbols": low_confidence_symbols[:20],
        "options_context_top_expected_move_symbols": expected_move_leaders,
        "options_context_top_skew_symbols": skew_leaders,
    }


def build_options_context_by_symbol(
    symbols: list[str],
    context_index: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        if not isinstance(symbol, str) or not symbol.strip():
            continue
        normalized = symbol.strip().upper()
        row = context_index.get(normalized)
        if row is None:
            result[normalized] = {
                "context_available": False,
                "reason_codes": ["options_context_missing"],
            }
            continue

        result[normalized] = {
            "context_available": True,
            "source_provider": row.get("source_provider"),
            "as_of_utc": row.get("as_of_utc"),
            "contract_count": row.get("contract_count"),
            "expiration_count": row.get("expiration_count"),
            "call_oi_total": row.get("call_oi_total"),
            "put_oi_total": row.get("put_oi_total"),
            "call_volume_total": row.get("call_volume_total"),
            "put_volume_total": row.get("put_volume_total"),
            "pcr_oi": row.get("pcr_oi"),
            "pcr_volume": row.get("pcr_volume"),
            "atm_iv": row.get("atm_iv"),
            "expected_move_1d_pct": row.get("expected_move_1d_pct"),
            "expected_move_1w_pct": row.get("expected_move_1w_pct"),
            "expected_move_30d_pct": row.get("expected_move_30d_pct"),
            "skew_25d_put_call_ratio": row.get("skew_25d_put_call_ratio"),
            "skew_25d_put_call_spread": row.get("skew_25d_put_call_spread"),
            "nonzero_bid_ask_ratio": row.get("nonzero_bid_ask_ratio"),
            "nonzero_open_interest_ratio": row.get("nonzero_open_interest_ratio"),
            "nonzero_delta_ratio": row.get("nonzero_delta_ratio"),
            "nonzero_iv_ratio": row.get("nonzero_iv_ratio"),
            "options_summary_regime": row.get("options_summary_regime"),
            "confidence_score": row.get("confidence_score"),
            "reason_codes": [],
        }

    return result
