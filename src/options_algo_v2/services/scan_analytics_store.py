from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_SCAN_ANALYTICS_DB_PATH = Path(
    os.getenv("MARKET_HISTORY_DB_PATH", "data/cache/market_history_watchlist60.db")
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@contextmanager
def get_connection(db_path: Path = DEFAULT_SCAN_ANALYTICS_DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        yield conn
        conn.commit()
    finally:
        conn.close()


def _ensure_scan_symbol_decisions_columns(conn: sqlite3.Connection) -> None:
    existing = {
        str(row[1])
        for row in conn.execute("PRAGMA table_info(scan_symbol_decisions)").fetchall()
    }
    if "blocking_reasons_json" not in existing:
        conn.execute("ALTER TABLE scan_symbol_decisions ADD COLUMN blocking_reasons_json TEXT")
    if "soft_penalty_reasons_json" not in existing:
        conn.execute("ALTER TABLE scan_symbol_decisions ADD COLUMN soft_penalty_reasons_json TEXT")
    if "options_context_borderline_score_pass" not in existing:
        conn.execute(
            "ALTER TABLE scan_symbol_decisions ADD COLUMN options_context_borderline_score_pass INTEGER"
        )
    if "options_context_borderline_score_pass_tier_a" not in existing:
        conn.execute(
            "ALTER TABLE scan_symbol_decisions ADD COLUMN options_context_borderline_score_pass_tier_a INTEGER"
        )
    if "options_context_borderline_score_pass_tier_b" not in existing:
        conn.execute(
            "ALTER TABLE scan_symbol_decisions ADD COLUMN options_context_borderline_score_pass_tier_b INTEGER"
        )
    if "options_context_borderline_rescue_tier" not in existing:
        conn.execute(
            "ALTER TABLE scan_symbol_decisions ADD COLUMN options_context_borderline_rescue_tier TEXT"
        )


def init_scan_analytics_store(
    db_path: Path = DEFAULT_SCAN_ANALYTICS_DB_PATH,
) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS scan_run_summary (
                run_id TEXT NOT NULL,
                timestamp_utc TEXT NOT NULL,
                runtime_mode TEXT,
                as_of_date TEXT,
                strict_live_mode INTEGER,
                degraded_live_mode INTEGER,
                used_mock_historical_fallback INTEGER,
                used_breadth_override INTEGER,
                used_placeholder_iv_inputs INTEGER,
                used_placeholder_iv_rank_inputs INTEGER,
                used_placeholder_iv_hv_ratio_inputs INTEGER,
                symbol_count INTEGER,
                passed_count INTEGER,
                rejected_count INTEGER,
                passed_symbols_json TEXT,
                rejected_symbols_json TEXT,
                top_trade_candidate_symbols_json TEXT,
                trade_idea_symbols_json TEXT,
                options_context_matched_count INTEGER,
                options_context_missing_count INTEGER,
                options_context_regime_counts_json TEXT,
                options_context_low_confidence_symbols_json TEXT,
                options_context_top_expected_move_symbols_json TEXT,
                options_context_top_skew_symbols_json TEXT,
                options_context_decision_adjusted_symbol_count INTEGER,
                options_context_hard_reject_count INTEGER,
                options_context_applied_reason_counts_json TEXT,
                rejection_reason_counts_json TEXT,
                signal_state_counts_json TEXT,
                strategy_type_counts_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (run_id)
            );

            CREATE TABLE IF NOT EXISTS scan_symbol_decisions (
                run_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timestamp_utc TEXT NOT NULL,
                runtime_mode TEXT,
                as_of_date TEXT,
                final_passed INTEGER,
                market_regime TEXT,
                directional_state TEXT,
                iv_state TEXT,
                signal_state TEXT,
                strategy_type TEXT,
                final_score REAL,
                min_score_required REAL,
                blocking_reasons_json TEXT,
                soft_penalty_reasons_json TEXT,
                rejection_reasons_json TEXT,
                rationale_json TEXT,
                close REAL,
                dma20 REAL,
                dma50 REAL,
                atr20 REAL,
                adx14 REAL,
                iv_rank REAL,
                iv_hv_ratio REAL,
                market_breadth_pct_above_20dma REAL,
                directional_checks_json TEXT,
                event_filter_json TEXT,
                extension_filter_json TEXT,
                liquidity_filter_json TEXT,
                feature_source_dataset TEXT,
                feature_source_schema TEXT,
                historical_row_provider TEXT,
                market_breadth_provider TEXT,
                trace_strategy_family TEXT,
                options_context_available INTEGER,
                options_context_source_provider TEXT,
                options_context_as_of_utc TEXT,
                options_contract_count INTEGER,
                options_expiration_count INTEGER,
                options_pcr_oi REAL,
                options_pcr_volume REAL,
                options_atm_iv REAL,
                options_expected_move_1d_pct REAL,
                options_expected_move_1w_pct REAL,
                options_expected_move_30d_pct REAL,
                options_skew_25d_put_call_ratio REAL,
                options_skew_25d_put_call_spread REAL,
                options_nonzero_bid_ask_ratio REAL,
                options_nonzero_open_interest_ratio REAL,
                options_nonzero_delta_ratio REAL,
                options_nonzero_iv_ratio REAL,
                options_summary_regime TEXT,
                options_confidence_score REAL,
                options_context_reason_codes_json TEXT,
                options_context_advisory_reason_codes_json TEXT,
                options_context_score_delta REAL,
                options_context_hard_reject INTEGER,
                options_context_final_score_after_context REAL,
                options_context_final_passed_after_context INTEGER,
                options_context_borderline_score_pass INTEGER,
                options_context_borderline_score_pass_tier_a INTEGER,
                options_context_borderline_score_pass_tier_b INTEGER,
                options_context_borderline_rescue_tier TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (run_id, symbol)
            );

            CREATE INDEX IF NOT EXISTS idx_scan_run_summary_as_of_date
            ON scan_run_summary (as_of_date);

            CREATE INDEX IF NOT EXISTS idx_scan_symbol_decisions_run_id
            ON scan_symbol_decisions (run_id);

            CREATE INDEX IF NOT EXISTS idx_scan_symbol_decisions_symbol
            ON scan_symbol_decisions (symbol);

            CREATE INDEX IF NOT EXISTS idx_scan_symbol_decisions_as_of_date
            ON scan_symbol_decisions (as_of_date);
            """
        )
        _ensure_scan_symbol_decisions_columns(conn)


def upsert_scan_run_summary_rows(
    *,
    rows: Iterable[dict[str, object]],
    db_path: Path = DEFAULT_SCAN_ANALYTICS_DB_PATH,
) -> int:
    payload_rows = list(rows)
    if not payload_rows:
        return 0

    init_scan_analytics_store(db_path)
    now = utc_now_iso()
    payload = []

    for row in payload_rows:
        payload.append(
            (
                str(row["run_id"]),
                str(row["timestamp_utc"]),
                row.get("runtime_mode"),
                row.get("as_of_date"),
                int(bool(row.get("strict_live_mode"))) if row.get("strict_live_mode") is not None else None,
                int(bool(row.get("degraded_live_mode"))) if row.get("degraded_live_mode") is not None else None,
                int(bool(row.get("used_mock_historical_fallback"))) if row.get("used_mock_historical_fallback") is not None else None,
                int(bool(row.get("used_breadth_override"))) if row.get("used_breadth_override") is not None else None,
                int(bool(row.get("used_placeholder_iv_inputs"))) if row.get("used_placeholder_iv_inputs") is not None else None,
                int(bool(row.get("used_placeholder_iv_rank_inputs"))) if row.get("used_placeholder_iv_rank_inputs") is not None else None,
                int(bool(row.get("used_placeholder_iv_hv_ratio_inputs"))) if row.get("used_placeholder_iv_hv_ratio_inputs") is not None else None,
                row.get("symbol_count"),
                row.get("passed_count"),
                row.get("rejected_count"),
                json.dumps(row.get("passed_symbols", []), sort_keys=True),
                json.dumps(row.get("rejected_symbols", []), sort_keys=True),
                json.dumps(row.get("top_trade_candidate_symbols", []), sort_keys=True),
                json.dumps(row.get("trade_idea_symbols", []), sort_keys=True),
                row.get("options_context_matched_count"),
                row.get("options_context_missing_count"),
                json.dumps(row.get("options_context_regime_counts", {}), sort_keys=True),
                json.dumps(row.get("options_context_low_confidence_symbols", []), sort_keys=True),
                json.dumps(row.get("options_context_top_expected_move_symbols", []), sort_keys=True),
                json.dumps(row.get("options_context_top_skew_symbols", []), sort_keys=True),
                row.get("options_context_decision_adjusted_symbol_count"),
                row.get("options_context_hard_reject_count"),
                json.dumps(row.get("options_context_applied_reason_counts", {}), sort_keys=True),
                json.dumps(row.get("rejection_reason_counts", {}), sort_keys=True),
                json.dumps(row.get("signal_state_counts", {}), sort_keys=True),
                json.dumps(row.get("strategy_type_counts", {}), sort_keys=True),
                now,
                now,
            )
        )

    with get_connection(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO scan_run_summary (
                run_id, timestamp_utc, runtime_mode, as_of_date,
                strict_live_mode, degraded_live_mode, used_mock_historical_fallback,
                used_breadth_override, used_placeholder_iv_inputs,
                used_placeholder_iv_rank_inputs, used_placeholder_iv_hv_ratio_inputs,
                symbol_count, passed_count, rejected_count,
                passed_symbols_json, rejected_symbols_json,
                top_trade_candidate_symbols_json, trade_idea_symbols_json,
                options_context_matched_count, options_context_missing_count,
                options_context_regime_counts_json,
                options_context_low_confidence_symbols_json,
                options_context_top_expected_move_symbols_json,
                options_context_top_skew_symbols_json,
                options_context_decision_adjusted_symbol_count,
                options_context_hard_reject_count,
                options_context_applied_reason_counts_json,
                rejection_reason_counts_json,
                signal_state_counts_json,
                strategy_type_counts_json,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                timestamp_utc=excluded.timestamp_utc,
                runtime_mode=excluded.runtime_mode,
                as_of_date=excluded.as_of_date,
                strict_live_mode=excluded.strict_live_mode,
                degraded_live_mode=excluded.degraded_live_mode,
                used_mock_historical_fallback=excluded.used_mock_historical_fallback,
                used_breadth_override=excluded.used_breadth_override,
                used_placeholder_iv_inputs=excluded.used_placeholder_iv_inputs,
                used_placeholder_iv_rank_inputs=excluded.used_placeholder_iv_rank_inputs,
                used_placeholder_iv_hv_ratio_inputs=excluded.used_placeholder_iv_hv_ratio_inputs,
                symbol_count=excluded.symbol_count,
                passed_count=excluded.passed_count,
                rejected_count=excluded.rejected_count,
                passed_symbols_json=excluded.passed_symbols_json,
                rejected_symbols_json=excluded.rejected_symbols_json,
                top_trade_candidate_symbols_json=excluded.top_trade_candidate_symbols_json,
                trade_idea_symbols_json=excluded.trade_idea_symbols_json,
                options_context_matched_count=excluded.options_context_matched_count,
                options_context_missing_count=excluded.options_context_missing_count,
                options_context_regime_counts_json=excluded.options_context_regime_counts_json,
                options_context_low_confidence_symbols_json=excluded.options_context_low_confidence_symbols_json,
                options_context_top_expected_move_symbols_json=excluded.options_context_top_expected_move_symbols_json,
                options_context_top_skew_symbols_json=excluded.options_context_top_skew_symbols_json,
                options_context_decision_adjusted_symbol_count=excluded.options_context_decision_adjusted_symbol_count,
                options_context_hard_reject_count=excluded.options_context_hard_reject_count,
                options_context_applied_reason_counts_json=excluded.options_context_applied_reason_counts_json,
                rejection_reason_counts_json=excluded.rejection_reason_counts_json,
                signal_state_counts_json=excluded.signal_state_counts_json,
                strategy_type_counts_json=excluded.strategy_type_counts_json,
                updated_at=excluded.updated_at
            """,
            payload,
        )

    return len(payload)


def upsert_scan_symbol_decisions(
    *,
    rows: Iterable[dict[str, object]],
    db_path: Path = DEFAULT_SCAN_ANALYTICS_DB_PATH,
) -> int:
    payload_rows = list(rows)
    if not payload_rows:
        return 0

    init_scan_analytics_store(db_path)
    now = utc_now_iso()
    payload = []

    for row in payload_rows:
        payload.append(
            (
                str(row["run_id"]),
                str(row["symbol"]),
                str(row["timestamp_utc"]),
                row.get("runtime_mode"),
                row.get("as_of_date"),
                int(bool(row.get("final_passed"))) if row.get("final_passed") is not None else None,
                row.get("market_regime"),
                row.get("directional_state"),
                row.get("iv_state"),
                row.get("signal_state"),
                row.get("strategy_type"),
                row.get("final_score"),
                row.get("min_score_required"),
                json.dumps(row.get("blocking_reasons", []), sort_keys=True),
                json.dumps(row.get("soft_penalty_reasons", []), sort_keys=True),
                json.dumps(row.get("rejection_reasons", []), sort_keys=True),
                json.dumps(row.get("rationale", []), sort_keys=True),
                row.get("close"),
                row.get("dma20"),
                row.get("dma50"),
                row.get("atr20"),
                row.get("adx14"),
                row.get("iv_rank"),
                row.get("iv_hv_ratio"),
                row.get("market_breadth_pct_above_20dma"),
                json.dumps(row.get("directional_checks", {}), sort_keys=True),
                json.dumps(row.get("event_filter", {}), sort_keys=True),
                json.dumps(row.get("extension_filter", {}), sort_keys=True),
                json.dumps(row.get("liquidity_filter", {}), sort_keys=True),
                row.get("feature_source_dataset"),
                row.get("feature_source_schema"),
                row.get("historical_row_provider"),
                row.get("market_breadth_provider"),
                row.get("trace_strategy_family"),
                int(bool(row.get("options_context_available"))) if row.get("options_context_available") is not None else None,
                row.get("options_context_source_provider"),
                row.get("options_context_as_of_utc"),
                row.get("options_contract_count"),
                row.get("options_expiration_count"),
                row.get("options_pcr_oi"),
                row.get("options_pcr_volume"),
                row.get("options_atm_iv"),
                row.get("options_expected_move_1d_pct"),
                row.get("options_expected_move_1w_pct"),
                row.get("options_expected_move_30d_pct"),
                row.get("options_skew_25d_put_call_ratio"),
                row.get("options_skew_25d_put_call_spread"),
                row.get("options_nonzero_bid_ask_ratio"),
                row.get("options_nonzero_open_interest_ratio"),
                row.get("options_nonzero_delta_ratio"),
                row.get("options_nonzero_iv_ratio"),
                row.get("options_summary_regime"),
                row.get("options_confidence_score"),
                json.dumps(row.get("options_context_reason_codes", []), sort_keys=True),
                json.dumps(row.get("options_context_advisory_reason_codes", []), sort_keys=True),
                row.get("options_context_score_delta"),
                int(bool(row.get("options_context_hard_reject"))) if row.get("options_context_hard_reject") is not None else None,
                row.get("options_context_final_score_after_context"),
                int(bool(row.get("options_context_final_passed_after_context"))) if row.get("options_context_final_passed_after_context") is not None else None,
                int(bool(row.get("options_context_borderline_score_pass"))) if row.get("options_context_borderline_score_pass") is not None else None,
                int(bool(row.get("options_context_borderline_score_pass_tier_a"))) if row.get("options_context_borderline_score_pass_tier_a") is not None else None,
                int(bool(row.get("options_context_borderline_score_pass_tier_b"))) if row.get("options_context_borderline_score_pass_tier_b") is not None else None,
                row.get("options_context_borderline_rescue_tier"),
                now,
                now,
            )
        )

    with get_connection(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO scan_symbol_decisions (
                run_id, symbol, timestamp_utc, runtime_mode, as_of_date,
                final_passed, market_regime, directional_state, iv_state, signal_state,
                strategy_type, final_score, min_score_required,
                blocking_reasons_json, soft_penalty_reasons_json,
                rejection_reasons_json, rationale_json,
                close, dma20, dma50, atr20, adx14, iv_rank, iv_hv_ratio,
                market_breadth_pct_above_20dma,
                directional_checks_json, event_filter_json, extension_filter_json, liquidity_filter_json,
                feature_source_dataset, feature_source_schema, historical_row_provider,
                market_breadth_provider, trace_strategy_family,
                options_context_available, options_context_source_provider,
                options_context_as_of_utc, options_contract_count, options_expiration_count,
                options_pcr_oi, options_pcr_volume, options_atm_iv,
                options_expected_move_1d_pct, options_expected_move_1w_pct, options_expected_move_30d_pct,
                options_skew_25d_put_call_ratio, options_skew_25d_put_call_spread,
                options_nonzero_bid_ask_ratio, options_nonzero_open_interest_ratio,
                options_nonzero_delta_ratio, options_nonzero_iv_ratio,
                options_summary_regime, options_confidence_score,
                options_context_reason_codes_json, options_context_advisory_reason_codes_json,
                options_context_score_delta, options_context_hard_reject,
                options_context_final_score_after_context, options_context_final_passed_after_context,
                options_context_borderline_score_pass, options_context_borderline_score_pass_tier_a,
                options_context_borderline_score_pass_tier_b, options_context_borderline_rescue_tier,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id, symbol) DO UPDATE SET
                timestamp_utc=excluded.timestamp_utc,
                runtime_mode=excluded.runtime_mode,
                as_of_date=excluded.as_of_date,
                final_passed=excluded.final_passed,
                market_regime=excluded.market_regime,
                directional_state=excluded.directional_state,
                iv_state=excluded.iv_state,
                signal_state=excluded.signal_state,
                strategy_type=excluded.strategy_type,
                final_score=excluded.final_score,
                min_score_required=excluded.min_score_required,
                blocking_reasons_json=excluded.blocking_reasons_json,
                soft_penalty_reasons_json=excluded.soft_penalty_reasons_json,
                rejection_reasons_json=excluded.rejection_reasons_json,
                rationale_json=excluded.rationale_json,
                close=excluded.close,
                dma20=excluded.dma20,
                dma50=excluded.dma50,
                atr20=excluded.atr20,
                adx14=excluded.adx14,
                iv_rank=excluded.iv_rank,
                iv_hv_ratio=excluded.iv_hv_ratio,
                market_breadth_pct_above_20dma=excluded.market_breadth_pct_above_20dma,
                directional_checks_json=excluded.directional_checks_json,
                event_filter_json=excluded.event_filter_json,
                extension_filter_json=excluded.extension_filter_json,
                liquidity_filter_json=excluded.liquidity_filter_json,
                feature_source_dataset=excluded.feature_source_dataset,
                feature_source_schema=excluded.feature_source_schema,
                historical_row_provider=excluded.historical_row_provider,
                market_breadth_provider=excluded.market_breadth_provider,
                trace_strategy_family=excluded.trace_strategy_family,
                options_context_available=excluded.options_context_available,
                options_context_source_provider=excluded.options_context_source_provider,
                options_context_as_of_utc=excluded.options_context_as_of_utc,
                options_contract_count=excluded.options_contract_count,
                options_expiration_count=excluded.options_expiration_count,
                options_pcr_oi=excluded.options_pcr_oi,
                options_pcr_volume=excluded.options_pcr_volume,
                options_atm_iv=excluded.options_atm_iv,
                options_expected_move_1d_pct=excluded.options_expected_move_1d_pct,
                options_expected_move_1w_pct=excluded.options_expected_move_1w_pct,
                options_expected_move_30d_pct=excluded.options_expected_move_30d_pct,
                options_skew_25d_put_call_ratio=excluded.options_skew_25d_put_call_ratio,
                options_skew_25d_put_call_spread=excluded.options_skew_25d_put_call_spread,
                options_nonzero_bid_ask_ratio=excluded.options_nonzero_bid_ask_ratio,
                options_nonzero_open_interest_ratio=excluded.options_nonzero_open_interest_ratio,
                options_nonzero_delta_ratio=excluded.options_nonzero_delta_ratio,
                options_nonzero_iv_ratio=excluded.options_nonzero_iv_ratio,
                options_summary_regime=excluded.options_summary_regime,
                options_confidence_score=excluded.options_confidence_score,
                options_context_reason_codes_json=excluded.options_context_reason_codes_json,
                options_context_advisory_reason_codes_json=excluded.options_context_advisory_reason_codes_json,
                options_context_score_delta=excluded.options_context_score_delta,
                options_context_hard_reject=excluded.options_context_hard_reject,
                options_context_final_score_after_context=excluded.options_context_final_score_after_context,
                options_context_final_passed_after_context=excluded.options_context_final_passed_after_context,
                options_context_borderline_score_pass=excluded.options_context_borderline_score_pass,
                options_context_borderline_score_pass_tier_a=excluded.options_context_borderline_score_pass_tier_a,
                options_context_borderline_score_pass_tier_b=excluded.options_context_borderline_score_pass_tier_b,
                options_context_borderline_rescue_tier=excluded.options_context_borderline_rescue_tier,
                updated_at=excluded.updated_at
            """,
            payload,
        )

    return len(payload)
