from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from options_algo_v2.models.options_context import OptionsContextSnapshot


def ensure_options_context_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS options_context_daily (
            symbol TEXT NOT NULL,
            as_of_date TEXT NOT NULL,
            as_of_utc TEXT NOT NULL,
            spot_price REAL,

            contract_count INTEGER,
            expiration_count INTEGER,
            atm_iv REAL,

            expected_move_1d_pct REAL,
            expected_move_1w_pct REAL,
            expected_move_30d_pct REAL,

            skew_25d_put_call_ratio REAL,
            skew_25d_put_call_spread REAL,

            call_oi_total INTEGER,
            put_oi_total INTEGER,
            call_volume_total INTEGER,
            put_volume_total INTEGER,
            pcr_oi REAL,
            pcr_volume REAL,

            nonzero_bid_ask_ratio REAL,
            nonzero_open_interest_ratio REAL,
            nonzero_delta_ratio REAL,
            nonzero_iv_ratio REAL,

            max_gamma_strike REAL,
            gamma_flip_estimate REAL,
            distance_to_gamma_flip_pct REAL,
            gex_per_1pct_move REAL,
            nearest_expiry_gamma_pct REAL,

            options_flow_regime TEXT,
            options_summary_regime TEXT,

            confidence_score REAL NOT NULL,
            confidence_reasons_json TEXT NOT NULL,
            missing_fields_json TEXT NOT NULL,
            source_provider TEXT NOT NULL,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            PRIMARY KEY (symbol, as_of_date)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_options_context_daily_symbol_date
        ON options_context_daily (symbol, as_of_date)
        """
    )
    conn.commit()


def _snapshot_to_row(snapshot: OptionsContextSnapshot) -> dict[str, object]:
    payload = asdict(snapshot)
    as_of_utc = str(payload["as_of_utc"])
    as_of_date = as_of_utc[:10]
    now_utc = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    return {
        "symbol": payload["symbol"],
        "as_of_date": as_of_date,
        "as_of_utc": as_of_utc,
        "spot_price": payload.get("spot_price"),

        "contract_count": payload.get("contract_count"),
        "expiration_count": payload.get("expiration_count"),
        "atm_iv": payload.get("atm_iv"),

        "expected_move_1d_pct": payload.get("expected_move_1d_pct"),
        "expected_move_1w_pct": payload.get("expected_move_1w_pct"),
        "expected_move_30d_pct": payload.get("expected_move_30d_pct"),

        "skew_25d_put_call_ratio": payload.get("skew_25d_put_call_ratio"),
        "skew_25d_put_call_spread": payload.get("skew_25d_put_call_spread"),

        "call_oi_total": payload.get("call_oi_total"),
        "put_oi_total": payload.get("put_oi_total"),
        "call_volume_total": payload.get("call_volume_total"),
        "put_volume_total": payload.get("put_volume_total"),
        "pcr_oi": payload.get("pcr_oi"),
        "pcr_volume": payload.get("pcr_volume"),

        "nonzero_bid_ask_ratio": payload.get("nonzero_bid_ask_ratio"),
        "nonzero_open_interest_ratio": payload.get("nonzero_open_interest_ratio"),
        "nonzero_delta_ratio": payload.get("nonzero_delta_ratio"),
        "nonzero_iv_ratio": payload.get("nonzero_iv_ratio"),

        "max_gamma_strike": payload.get("max_gamma_strike"),
        "gamma_flip_estimate": payload.get("gamma_flip_estimate"),
        "distance_to_gamma_flip_pct": payload.get("distance_to_gamma_flip_pct"),
        "gex_per_1pct_move": payload.get("gex_per_1pct_move"),
        "nearest_expiry_gamma_pct": payload.get("nearest_expiry_gamma_pct"),

        "options_flow_regime": payload.get("options_flow_regime"),
        "options_summary_regime": payload.get("options_summary_regime"),

        "confidence_score": payload.get("confidence_score", 0.0),
        "confidence_reasons_json": json.dumps(payload.get("confidence_reasons", []), sort_keys=True),
        "missing_fields_json": json.dumps(payload.get("missing_fields", []), sort_keys=True),
        "source_provider": payload.get("source_provider", ""),

        "created_at": now_utc,
        "updated_at": now_utc,
    }


def upsert_options_context_snapshots(
    *,
    db_path: str | Path,
    snapshots: list[OptionsContextSnapshot],
) -> Path:
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_file))
    try:
        ensure_options_context_table(conn)

        rows = [_snapshot_to_row(snapshot) for snapshot in snapshots]
        conn.executemany(
            """
            INSERT INTO options_context_daily (
                symbol,
                as_of_date,
                as_of_utc,
                spot_price,

                contract_count,
                expiration_count,
                atm_iv,

                expected_move_1d_pct,
                expected_move_1w_pct,
                expected_move_30d_pct,

                skew_25d_put_call_ratio,
                skew_25d_put_call_spread,

                call_oi_total,
                put_oi_total,
                call_volume_total,
                put_volume_total,
                pcr_oi,
                pcr_volume,

                nonzero_bid_ask_ratio,
                nonzero_open_interest_ratio,
                nonzero_delta_ratio,
                nonzero_iv_ratio,

                max_gamma_strike,
                gamma_flip_estimate,
                distance_to_gamma_flip_pct,
                gex_per_1pct_move,
                nearest_expiry_gamma_pct,

                options_flow_regime,
                options_summary_regime,

                confidence_score,
                confidence_reasons_json,
                missing_fields_json,
                source_provider,

                created_at,
                updated_at
            ) VALUES (
                :symbol,
                :as_of_date,
                :as_of_utc,
                :spot_price,

                :contract_count,
                :expiration_count,
                :atm_iv,

                :expected_move_1d_pct,
                :expected_move_1w_pct,
                :expected_move_30d_pct,

                :skew_25d_put_call_ratio,
                :skew_25d_put_call_spread,

                :call_oi_total,
                :put_oi_total,
                :call_volume_total,
                :put_volume_total,
                :pcr_oi,
                :pcr_volume,

                :nonzero_bid_ask_ratio,
                :nonzero_open_interest_ratio,
                :nonzero_delta_ratio,
                :nonzero_iv_ratio,

                :max_gamma_strike,
                :gamma_flip_estimate,
                :distance_to_gamma_flip_pct,
                :gex_per_1pct_move,
                :nearest_expiry_gamma_pct,

                :options_flow_regime,
                :options_summary_regime,

                :confidence_score,
                :confidence_reasons_json,
                :missing_fields_json,
                :source_provider,

                :created_at,
                :updated_at
            )
            ON CONFLICT(symbol, as_of_date) DO UPDATE SET
                as_of_utc=excluded.as_of_utc,
                spot_price=excluded.spot_price,

                contract_count=excluded.contract_count,
                expiration_count=excluded.expiration_count,
                atm_iv=excluded.atm_iv,

                expected_move_1d_pct=excluded.expected_move_1d_pct,
                expected_move_1w_pct=excluded.expected_move_1w_pct,
                expected_move_30d_pct=excluded.expected_move_30d_pct,

                skew_25d_put_call_ratio=excluded.skew_25d_put_call_ratio,
                skew_25d_put_call_spread=excluded.skew_25d_put_call_spread,

                call_oi_total=excluded.call_oi_total,
                put_oi_total=excluded.put_oi_total,
                call_volume_total=excluded.call_volume_total,
                put_volume_total=excluded.put_volume_total,
                pcr_oi=excluded.pcr_oi,
                pcr_volume=excluded.pcr_volume,

                nonzero_bid_ask_ratio=excluded.nonzero_bid_ask_ratio,
                nonzero_open_interest_ratio=excluded.nonzero_open_interest_ratio,
                nonzero_delta_ratio=excluded.nonzero_delta_ratio,
                nonzero_iv_ratio=excluded.nonzero_iv_ratio,

                max_gamma_strike=excluded.max_gamma_strike,
                gamma_flip_estimate=excluded.gamma_flip_estimate,
                distance_to_gamma_flip_pct=excluded.distance_to_gamma_flip_pct,
                gex_per_1pct_move=excluded.gex_per_1pct_move,
                nearest_expiry_gamma_pct=excluded.nearest_expiry_gamma_pct,

                options_flow_regime=excluded.options_flow_regime,
                options_summary_regime=excluded.options_summary_regime,

                confidence_score=excluded.confidence_score,
                confidence_reasons_json=excluded.confidence_reasons_json,
                missing_fields_json=excluded.missing_fields_json,
                source_provider=excluded.source_provider,
                updated_at=excluded.updated_at
            """,
            rows,
        )
        conn.commit()
    finally:
        conn.close()

    return db_file
