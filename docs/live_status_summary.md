# live_status_summary

## Current status

The repository is currently operating successfully as a:

- **paper-live validated**
- **SQLite-audited**
- **production-like analytics**
options signal platform.

Canonical references:
- Branch: `epic2-sqlite-first`
- Completion tag: `epic1-5-complete`

---

## What is stable now

The following are verified working together:

- watchlist-driven scan execution
- paper-live run logging
- scan artifact generation under `data/scan_results/`
- run-level SQLite persistence into `scan_run_summary`
- symbol-level SQLite persistence into `scan_symbol_decisions`
- historical backfill from scan JSON artifacts
- options-context score adjustment
- borderline rescue logic
- Tier A / Tier B mutual exclusivity in persisted rows
- pre-context score / gap persistence
- effective soft-penalties persistence
- review reporting with uplift / rescue metrics

Primary analytics DB:
- `data/cache/market_history_watchlist60.db`

---

## What is not implied by this status

This status does **not** mean:
- unattended live trading is enabled
- execution simulation is fully implemented
- broker execution is wired for autonomous deployment

The stable operating posture is:
- repeated paper-live scans
- analytics review
- rescue-behavior audit
- historical backfill and validation

---

## Historical analytics note

Historical rows span multiple schema / metadata eras.

### Older rows
May have:
- missing rescue metadata
- missing pre-context fields

### Transitional rows
May have:
- rescue metadata
- partial audit fields

### Current stable rows
Include:
- `options_context_pre_context_score`
- `options_context_pre_context_score_gap`
- `options_context_effective_soft_penalties_json`
- normalized rescue-tier fields

Audit-field-complete rows begin around:
- `scan_20260412T194542Z`

---

## Recommended daily workflow

1. Run:
   - `scripts/run_paper_live_daily.py`
2. Inspect latest run in SQLite:
   - `scan_run_summary`
   - `scan_symbol_decisions`
3. Validate BAC / NFLX / CRM or target symbols
4. Run:
   - `scripts/review_scan_analytics_sqlite.py`
5. Optionally run:
   - `scripts/backfill_scan_analytics_sqlite.py`

---

## Current conclusion

EPIC 1 through EPIC 5 are complete for the current paper-live + SQLite analytics operating model.

Remaining work, if desired, is future enhancement work:
- live execution hardening
- stricter go-live gating
- simulation / paper execution modeling
- dashboard / reporting expansion
- candidate-only review modes

