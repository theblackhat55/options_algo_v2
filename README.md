# options_algo_v2

A watchlist-driven options strategy platform that scans underlyings, evaluates market / technical / volatility context, applies options-context adjustments, selects spread candidates, and produces explainable trade ideas.

The project is currently operated as a **paper-live validated signal platform with SQLite analytics**.

---

## Current operating status

EPIC 1 through EPIC 5 are complete on the current working branch.

Canonical references:
- **Branch:** `epic2-sqlite-first`
- **Completion tag:** `epic1-5-complete`

What is working end-to-end:
- watchlist-driven scans
- paper-live artifact generation
- paper-live JSONL / CSV logging
- SQLite persistence of run-level and symbol-level analytics
- historical backfill from scan JSON artifacts into SQLite
- options-context rescue logic with Tier A / Tier B handling
- mutual exclusivity of rescue tiers in persisted analytics
- persistence of pre-context score, pre-context gap, effective soft penalties, and rescue tier
- review analytics with pre-context score, uplift, and rescue-tier reporting

Primary analytics database:
- `data/cache/market_history_watchlist60.db`

Primary analytics tables:
- `scan_run_summary`
- `scan_symbol_decisions`

Important historical note:
- rows before the final audit-field rollout may contain partial or missing rescue metadata
- audit-field-complete rows begin around:
  - `scan_20260412T194542Z`

---

## What this repo does

The pipeline runs left-to-right in this order:

1. **Universe / watchlist input** — watchlist JSON under `data/watchlists/`
2. **Historical bar features** — Databento daily OHLCV → `close`, `dma20`, `dma50`, `atr20`, `adx14`, `rsi14`, `hv20`
3. **Market breadth + regime** — breadth-informed regime classification
4. **Options chain** — Polygon live snapshots normalized to `bid/ask/mid/delta/open_interest/volume/iv`
5. **Volatility context**
   - `iv_hv_ratio`
   - `iv_rank`
6. **Market regime classifier** — `TREND_UP`, `TREND_DOWN`, `RANGE_UNCLEAR`, `RISK_OFF`
7. **Directional state classifier**
8. **IV state classifier** — `IV_RICH`, `IV_NORMAL`, `IV_CHEAP`
9. **Strategy selector** — one of:
   - `BULL_PUT_SPREAD`
   - `BULL_CALL_SPREAD`
   - `BEAR_CALL_SPREAD`
   - `BEAR_PUT_SPREAD`
10. **Hard filters** — event, liquidity, extension
11. **Candidate scoring** — final score with thresholding
12. **Options context layer** — confidence / PCR / skew / expected move / coverage adjustments
13. **Borderline rescue logic** — Tier A / Tier B rescue policy when eligible
14. **Spread selection**
15. **Trade idea generation + artifact writing**
16. **Paper-live logging + SQLite analytics persistence**

---

## Repository layout

### Config
- `config/strategy_v1.yaml` — strategy / scoring / DTE / delta / threshold configuration
- `config/universe_v1.yaml` — universe configuration
- `config/risk_v1.yaml` — liquidity / quote freshness / risk limits

### Core services
- `src/options_algo_v2/services/options_context_decision_adjuster.py`
  - applies options-context score deltas
  - handles hard rejects
  - emits rescue debug / audit fields
- `src/options_algo_v2/services/paper_live_logger.py`
  - writes paper-live JSONL / CSV logs
  - builds symbol rows persisted into analytics
- `src/options_algo_v2/services/scan_analytics_store.py`
  - SQLite schema management and upserts

### Key scripts
- `scripts/run_paper_live_daily.py` — paper-live scan + persistence
- `scripts/backfill_scan_analytics_sqlite.py` — backfill scan JSON artifacts into SQLite
- `scripts/review_scan_analytics_sqlite.py` — review recent runs from SQLite
- `scripts/run_nightly_scan.py` — core scan entry point
- `scripts/run_trade_ideas.py` — scan + trade ideas
- `scripts/inspect_scan_debug.py` — inspect scan artifacts
- `scripts/inspect_scan_result.py` — inspect scan output
- `scripts/review_paper_live_logs.py` — legacy JSONL/CSV review path
- `scripts/paper_live_symbol_leaderboard.py` — legacy symbol-frequency review path

### Output directories
- `data/scan_results/` — scan artifacts
- `data/watchlists/` — watchlist JSON files
- `data/validation/` — paper-live JSONL / CSV logs
- `data/cache/` — SQLite analytics database

---

## Quick start

### 1) Create and activate environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2) Load environment variables
```bash
set -a
source .env
set +a
```

Typical live / paper-live dependencies:
```bash
export OPTIONS_ALGO_RUNTIME_MODE=live
export DATABENTO_API_KEY=...
export POLYGON_API_KEY=...
```

### 3) Run one paper-live scan
```bash
export POLYGON_TIMEOUT_SECONDS=30

python3 scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/options_watchlist_filtered_20260323T144511Z.json \
  --end-date 2026-03-21
```

### 4) Verify latest run in SQLite
```bash
DB=data/cache/market_history_watchlist60.db
LATEST_RUN_ID="$(sqlite3 "$DB" "select run_id from scan_run_summary order by timestamp_utc desc limit 1;")"
echo "LATEST_RUN_ID=$LATEST_RUN_ID"

sqlite3 "$DB" "
SELECT run_id,
       symbol,
       final_passed,
       final_score,
       min_score_required,
       options_context_pre_context_score,
       options_context_pre_context_score_gap,
       options_context_borderline_score_pass,
       options_context_borderline_score_pass_tier_a,
       options_context_borderline_score_pass_tier_b,
       options_context_borderline_rescue_tier,
       options_context_effective_soft_penalties_json
FROM scan_symbol_decisions
WHERE run_id = '$LATEST_RUN_ID'
ORDER BY symbol;
"
```

### 5) Review recent analytics
```bash
python3 scripts/review_scan_analytics_sqlite.py \
  --limit-runs 20 \
  --symbols BAC NFLX CRM
```

---

## Daily operator loop

```bash
export POLYGON_TIMEOUT_SECONDS=30

python3 scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/options_watchlist_filtered_20260323T144511Z.json \
  --end-date 2026-03-21

DB=data/cache/market_history_watchlist60.db
LATEST_RUN_ID="$(sqlite3 "$DB" "select run_id from scan_run_summary order by timestamp_utc desc limit 1;")"
echo "LATEST_RUN_ID=$LATEST_RUN_ID"

sqlite3 "$DB" "
SELECT run_id,
       symbol,
       final_passed,
       final_score,
       options_context_pre_context_score,
       options_context_pre_context_score_gap,
       options_context_borderline_rescue_tier,
       options_context_effective_soft_penalties_json
FROM scan_symbol_decisions
WHERE run_id = '$LATEST_RUN_ID'
  AND symbol IN ('BAC','NFLX','CRM')
ORDER BY symbol;
"

python3 scripts/review_scan_analytics_sqlite.py \
  --limit-runs 20 \
  --symbols BAC NFLX CRM
```

---

## SQLite analytics model

Database:
- `data/cache/market_history_watchlist60.db`

### `scan_run_summary`
Run-level persistence including:
- `run_id`
- timestamps / mode fields
- summary counts
- top trade candidates
- options-context run metadata

### `scan_symbol_decisions`
Per-symbol persistence including:
- `final_passed`
- `final_score`
- `min_score_required`
- blocking / soft-penalty reasons
- context diagnostics
- rescue-tier flags
- pre-context audit fields

Important fields:
- `options_context_pre_context_score`
- `options_context_pre_context_score_gap`
- `options_context_effective_soft_penalties_json`
- `options_context_borderline_score_pass`
- `options_context_borderline_score_pass_tier_a`
- `options_context_borderline_score_pass_tier_b`
- `options_context_borderline_rescue_tier`

---

## Backfill workflow

Backfill all or part of historical scan artifacts into SQLite.

### Backfill a specific run
```bash
python3 scripts/backfill_scan_analytics_sqlite.py --run-ids scan_20260412T194542Z
```

### Backfill recent runs
```bash
python3 scripts/backfill_scan_analytics_sqlite.py --limit 30
```

### Backfill all matching scan artifacts
```bash
python3 scripts/backfill_scan_analytics_sqlite.py
```

---

## Rescue logic notes

The options-context layer supports rescue behavior for borderline candidates.

### Tier A
Intended for stronger borderline cases that become acceptable after context uplift.

### Tier B
Intended for narrower rescue cases and is persisted as **mutually exclusive** with Tier A.

### Persistence guarantees
Persisted rows should never show both:
- `options_context_borderline_score_pass_tier_a = 1`
- `options_context_borderline_score_pass_tier_b = 1`

Validation query:
```bash
DB=data/cache/market_history_watchlist60.db

sqlite3 "$DB" "
SELECT run_id,
       symbol,
       final_score,
       options_context_borderline_score_pass_tier_a,
       options_context_borderline_score_pass_tier_b,
       options_context_borderline_rescue_tier
FROM scan_symbol_decisions
WHERE options_context_borderline_score_pass_tier_a = 1
  AND options_context_borderline_score_pass_tier_b = 1
ORDER BY timestamp_utc DESC, symbol;
"
```

Expected result: **no rows**

---

## Current operating posture

This repository should currently be treated as a:
- **paper-live validated**
- **SQLite-audited**
- **production-like analytics**
signal platform

It is suitable for:
- repeated watchlist scans
- paper-live validation
- run-by-run analytics
- rescue-behavior review
- historical backfill and audit

It is **not yet documented here as unattended live execution infrastructure**.

---

## Development

```bash
pytest
ruff check .
mypy src
```

---

## Documentation

- `docs/OPERATOR_QUICKSTART.md` — short daily operator workflow
- `docs/RUNBOOK.md` — operational runbook and validation queries
- `docs/live_status_summary.md` — current live / paper-live status
- `docs/IMPLEMENTATION_TRACKER.md` — implementation completion tracker
- `docs/strategy.md` — strategy and decision logic
- `docs/rulebook.md` — deterministic rulebook / spec
- `docs/watchlist_design.md` — watchlist design
- `docs/options_watchlist_policy.md` — options-watchlist policy
- `docs/go_live_phases.md` — staged go-live plan
- `docs/dashboard_integration.md` — dashboard consumers / schema notes
- `docs/vision.md` — long-term platform vision

