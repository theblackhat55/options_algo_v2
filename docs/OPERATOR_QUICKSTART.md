# OPERATOR QUICKSTART

This is the shortest practical daily workflow for the current paper-live + SQLite analytics stack.

Canonical references:
- Branch: `epic2-sqlite-first`
- Stable umbrella tag: `epic1-5-complete`

Primary analytics DB:
- `data/cache/market_history_watchlist60.db`

---

## 1) Activate environment

```bash
source .venv/bin/activate
set -a
source .env
set +a
export POLYGON_TIMEOUT_SECONDS=30
```

---

## 2) Run a paper-live scan

```bash
python3 scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/options_watchlist_filtered_20260323T144511Z.json \
  --end-date 2026-03-21
```

Expected output includes:
- `logged_run_id=...`
- `persisted_scan_run_summary_count=1`
- `persisted_scan_symbol_decision_count=15`

---

## 3) Get latest run ID

```bash
DB=data/cache/market_history_watchlist60.db
LATEST_RUN_ID="$(sqlite3 "$DB" "select run_id from scan_run_summary order by timestamp_utc desc limit 1;")"
echo "LATEST_RUN_ID=$LATEST_RUN_ID"
```

---

## 4) Inspect key symbols

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

What to look for:
- `final_score`
- `options_context_pre_context_score`
- `options_context_pre_context_score_gap`
- `options_context_borderline_rescue_tier`
- `options_context_effective_soft_penalties_json`

---

## 5) Check rescue-tier exclusivity

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
- **no rows**

---

## 6) Review recent analytics

```bash
python3 scripts/review_scan_analytics_sqlite.py \
  --limit-runs 20 \
  --symbols BAC NFLX CRM
```

Review output includes:
- appearances / passes / fails
- avg final score
- avg score gap
- avg pre-context score
- avg pre-context gap
- avg score uplift
- soft-penalty totals
- rescue-tier counts

Note:
- the review script excludes zero pre-context rows from uplift / pre-context averages

---

## 7) Optional backfill

### Re-backfill the latest run
```bash
python3 scripts/backfill_scan_analytics_sqlite.py --run-ids "$LATEST_RUN_ID"
```

### Backfill recent runs
```bash
python3 scripts/backfill_scan_analytics_sqlite.py --limit 30
```

---

## 8) Historical note

Older rows may exist in three eras:
1. rows with missing rescue metadata
2. rows with partial rescue metadata
3. rows with full audit fields

Audit-field-complete rows begin around:
- `scan_20260412T194542Z`

Interpret uplift and rescue analytics primarily from that era forward.

