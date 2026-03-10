from __future__ import annotations

from typing import cast

from options_algo_v2.services.trade_candidate_ranking import score_trade_candidate


def build_top_trade_summary_rows(
    candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for candidate in candidates:
        expiration = str(candidate.get("expiration", ""))
        net_credit_value = cast(
            float | int | str,
            candidate.get("net_credit", 0.0) or 0.0,
        )
        width_value = cast(
            float | int | str,
            candidate.get("width", 0.0) or 0.0,
        )

        rows.append(
            {
                "symbol": str(candidate.get("symbol", "unknown")),
                "strategy_family": str(
                    candidate.get("strategy_family", "unknown")
                ),
                "expiration": expiration,
                "net_credit": float(net_credit_value),
                "width": float(width_value),
                "score": score_trade_candidate(candidate),
            }
        )

    return rows
