from __future__ import annotations

import json
import sys
from pathlib import Path


def _fmt(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: PYTHONPATH=src python scripts/inspect_scan_debug.py <scan_result.json>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"error: file not found: {path}")
        return 1

    payload = json.loads(path.read_text())
    runtime_metadata = payload.get("runtime_metadata", {})
    summary = payload.get("summary", {})
    decisions = payload.get("decisions", [])
    feature_debug_by_symbol = runtime_metadata.get("feature_debug_by_symbol", {})
    decision_trace_by_symbol = runtime_metadata.get("decision_trace_by_symbol", {})

    decisions_by_symbol = {}
    for item in decisions:
        symbol = item.get("symbol")
        if isinstance(symbol, str) and symbol:
            decisions_by_symbol[symbol] = item

    print(f"path={path}")
    print(f"run_id={payload.get('run_id')}")
    print(f"summary={summary}")
    print()

    symbols = sorted(
        set(feature_debug_by_symbol.keys())
        | set(decision_trace_by_symbol.keys())
        | set(decisions_by_symbol.keys())
    )

    for symbol in symbols:
        feat = feature_debug_by_symbol.get(symbol, {})
        trace = decision_trace_by_symbol.get(symbol, {})
        decision = decisions_by_symbol.get(symbol, {})

        print(symbol)
        print(
            "  source:"
            f" dataset={_fmt(feat.get('dataset'))}"
            f" schema={_fmt(feat.get('schema'))}"
            f" historical_row_provider={_fmt(feat.get('historical_row_provider'))}"
            f" market_breadth_provider={_fmt(feat.get('market_breadth_provider'))}"
        )
        print(
            "  raw_features:"
            f" close={_fmt(decision.get('close'))}"
            f" dma20={_fmt(decision.get('dma20'))}"
            f" dma50={_fmt(decision.get('dma50'))}"
            f" atr20={_fmt(decision.get('atr20'))}"
            f" adx14={_fmt(decision.get('adx14'))}"
            f" iv_rank={_fmt(decision.get('iv_rank'))}"
            f" iv_hv_ratio={_fmt(decision.get('iv_hv_ratio'))}"
            f" breadth20dma={_fmt(decision.get('market_breadth_pct_above_20dma'))}"
        )
        print(f"  directional_checks={decision.get('directional_checks')}")
        print(
            "  decision:"
            f" directional_state={_fmt(trace.get('directional_state'))}"
            f" market_regime={_fmt(trace.get('market_regime'))}"
            f" iv_state={_fmt(trace.get('iv_state'))}"
            f" signal_state={_fmt(trace.get('signal_state'))}"
            f" strategy_type={_fmt(trace.get('strategy_type'))}"
            f" final_passed={_fmt(trace.get('final_passed'))}"
            f" final_score={_fmt(trace.get('final_score'))}"
            f" min_score_required={_fmt(trace.get('min_score_required'))}"
        )
        print(f"  rationale={trace.get('rationale')}")
        print(f"  rejection_reasons={trace.get('rejection_reasons', [])}")
        print(f"  event_filter={trace.get('event_filter')}")
        print(f"  extension_filter={trace.get('extension_filter')}")
        print(f"  liquidity_filter={trace.get('liquidity_filter')}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
