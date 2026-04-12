# RUNBOOK

Operational runbook for the current paper-live + SQLite analytics workflow.

Canonical references:
- Branch: `epic2-sqlite-first`
- Completion tag: `epic1-5-complete`

Primary analytics DB:
- `data/cache/market_history_watchlist60.db`

---

## 1) Runtime prerequisites

```bash
source .venv/bin/activate
set -a
source .env
set +a
export POLYGON_TIMEOUT_SECONDS=30
```

Expected environment:
- `DATABENTO_API_KEY`
- `POLYGON_API_KEY`
- `OPTIONS_ALGO_RUNTIME_MODE=live`

---

## 2) Health check: compile critical files

```bash
python3 -m py_compile \
  src/options_algo_v2/services/paper_live_logger.py \
  src/options_algo_v2/services/options_context_decision_adjuster.py \
  src/options_algo_v2/services/scan_analytics_store.py \
  scripts/backfill_scan_analytics_sqlite.py \
  scripts/review_scan_analytics_sqlite.py
```

---

## 3) Run a fresh paper-live scan

```bash
python3 scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/options_watchlist_filtered_20260323T144511Z.json \
  --end-date 2026-03-21
```

Expected outputs:
- `logged_run_id=...`
- `persisted_scan_run_summary_count=1`
- `persisted_scan_symbol_decision_count=15`

Artifacts:
- `data/scan_results/scan_<run_id>.json`
- `data/validation/paper_live_runs.jsonl`
- `data/validation/paper_live_symbol_decisions.jsonl`
- `data/validation/paper_live_runs.csv`

---

## 4) Identify the latest run in SQLite

```bash
DB=data/cache/market_history_watchlist60.db
LATEST_RUN_ID="$(sqlite3 "$DB" "select run_id from scan_run_summary order by timestamp_utc desc limit 1;")"
echo "LATEST_RUN_ID=$LATEST_RUN_ID"
```

---

## 5) Validate run-level persistence

```bash
sqlite3 "$DB" "
SELECT run_id, timestamp_utc
FROM scan_run_summary
WHERE run_id = '$LATEST_RUN_ID';
"
```

Expected:
- exactly one row

---

## 6) Validate symbol-level persistence

```bash
sqlite3 "$DB" "
SELECT count(*)
FROM scan_symbol_decisions
WHERE run_id = '$LATEST_RUN_ID';
"
```

Expected:
- `15`

---

## 7) Inspect key symbol rows

```bash
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
  AND symbol IN ('BAC','NFLX','CRM')
ORDER BY symbol;
"
```

Interpretation:
- `final_score` is the post-context stored score
- `options_context_pre_context_score` is the pre-context score used for audit
- `options_context_pre_context_score_gap` is the threshold gap before rescue/uplift
- `options_context_effective_soft_penalties_json` stores effective soft penalties
- `options_context_borderline_rescue_tier` shows `A`, `B`, or null

---

## 8) Validate rescue-tier exclusivity

No row should have both Tier A and Tier B flags set.

```bash
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

Expected result:
- no rows

---

## 9) Review recent analytics

```bash
python3 scripts/review_scan_analytics_sqlite.py \
  --limit-runs 20 \
  --symbols BAC NFLX CRM
```

The review script reports:
- appearances
- passes / fails
- avg final score
- avg score gap
- avg pre-context score
- avg pre-context gap
- avg score uplift
- blocking reason counts
- soft-penalty reason counts
- top trade candidates
- rescue-tier counts

Note:
- zero pre-context rows are excluded from pre-context / uplift averages

---

## 10) Backfill workflows

### Backfill one run
```bash
python3 scripts/backfill_scan_analytics_sqlite.py --run-ids "$LATEST_RUN_ID"
```

### Backfill recent runs
```bash
python3 scripts/backfill_scan_analytics_sqlite.py --limit 30
```

### Backfill all scan artifacts
```bash
python3 scripts/backfill_scan_analytics_sqlite.py
```

Backfill source:
- `data/scan_results/scan_*.json`

Backfill destination:
- `data/cache/market_history_watchlist60.db`

---

## 11) Historical data note

Historical analytics currently span multiple metadata eras:

### Era 1
Older rows may have:
- missing rescue metadata
- missing pre-context fields

### Era 2
Middle rows may have:
- rescue tier and soft penalties
- partial audit fields

### Era 3
Current stable rows have:
- `options_context_pre_context_score`
- `options_context_pre_context_score_gap`
- `options_context_effective_soft_penalties_json`
- normalized rescue-tier persistence

Audit-field-complete era begins around:
- `scan_20260412T194542Z`

For uplift and rescue analysis, prioritize era 3.

---

## 12) Failure patterns to watch

### Run completes but BAC / CRM / NFLX show zeros
This may be legitimate if the market / regime / candidate selection produced:
- non-candidate rows
- final scores near zero
- no rescue flags

That does **not** automatically indicate a bug.

### Overlapping rescue tiers
If any row shows both:
- `options_context_borderline_score_pass_tier_a = 1`
- `options_context_borderline_score_pass_tier_b = 1`

then persistence normalization or backfill logic regressed.

### Missing persisted audit fields for new runs
If new runs are missing:
- pre-context score
- pre-context gap
- effective soft penalties

inspect:
- `options_context_decision_adjuster.py`
- `paper_live_logger.py`
- `scan_analytics_store.py`

---

## 13) Canonical stable references

- branch: `epic2-sqlite-first`
- umbrella completion tag: `epic1-5-complete`

Additional milestone tags may exist for:
- rescue-tier normalization
- pre-context audit fields
- uplift review filtering

