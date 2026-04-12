# IMPLEMENTATION TRACKER

## Current implementation state

Canonical references:
- Branch: `epic2-sqlite-first`
- Completion tag: `epic1-5-complete`

---

## EPIC 1 — Scan generation and paper-live flow
**Status:** Complete

Implemented:
- watchlist-driven scans
- scan artifact generation
- paper-live daily run flow
- JSONL / CSV logging

---

## EPIC 2 — SQLite analytics persistence
**Status:** Complete

Implemented:
- `scan_run_summary` persistence
- `scan_symbol_decisions` persistence
- schema migration support
- upsert-based write path
- backfill utility:
  - `scripts/backfill_scan_analytics_sqlite.py`

Primary DB:
- `data/cache/market_history_watchlist60.db`

---

## EPIC 3 — Options-context integration
**Status:** Complete

Implemented:
- options-context scoring adjustments
- hard reject path
- context diagnostics
- confidence / regime / PCR / skew / expected move adjustments
- effective soft-penalty persistence

---

## EPIC 4 — Review and analytics reporting
**Status:** Complete

Implemented:
- SQLite review script
- per-symbol summary reporting
- blocking reason totals
- soft-penalty totals
- rescue-tier counts
- repeated candidate reporting
- pre-context score / gap / uplift reporting

Key script:
- `scripts/review_scan_analytics_sqlite.py`

---

## EPIC 5 — Borderline rescue logic and auditability
**Status:** Complete

Implemented:
- Tier A rescue logic
- Tier B rescue logic
- mutual exclusivity between Tier A and Tier B
- persisted rescue-tier normalization
- pre-context score audit fields
- pre-context gap audit fields
- effective soft-penalties audit fields
- uplift-aware review reporting
- zero-pre-context filtering for uplift averages

Important persisted fields:
- `options_context_pre_context_score`
- `options_context_pre_context_score_gap`
- `options_context_effective_soft_penalties_json`
- `options_context_borderline_score_pass`
- `options_context_borderline_score_pass_tier_a`
- `options_context_borderline_score_pass_tier_b`
- `options_context_borderline_rescue_tier`

---

## Historical data note

Historical rows span multiple metadata eras.

Audit-field-complete rows begin around:
- `scan_20260412T194542Z`

Use that era forward for the cleanest uplift / rescue analytics.

---

## Verified operating loop

The following loop has been validated:

1. run paper-live scan
2. persist run + symbol rows into SQLite
3. inspect latest run via SQLite queries
4. backfill from stored scan artifacts
5. review recent runs with uplift / rescue metrics
6. validate no overlapping rescue-tier flags

---

## Remaining work

No blocking implementation items remain for EPIC 1–5.

Future enhancements only:
- candidate-only analytics mode in review script
- stricter live / go-live hardening
- simulation / execution modeling
- dashboard enhancements
- documentation polish beyond current operational alignment

