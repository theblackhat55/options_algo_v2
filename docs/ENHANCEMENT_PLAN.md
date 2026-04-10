	# options_algo_v2 Enhancement Plan

Status: Draft  
Owner: @theblackhat55  
Last updated: 2026-04-10

---

## 1) Purpose

This plan defines the next-stage enhancement roadmap for `options_algo_v2` based on:

1. live paper-run artifact review
2. scan-result JSON analysis
3. options-context integration status
4. operational needs for reproducibility, performance review, and lower provider dependency

The goal is to evolve the project from a functioning paper-live selector into a more reliable, auditable, and optimizable decision engine.

---

## 2) What we learned from recent live artifact review

A clean live subset was analyzed from scan JSON artifacts.

### Clean live subset summary
- 27 live Databento-backed runs
- 945 candidates
- 128 passed
- 118 trade ideas
- pass rate: 13.5%
- suspicious live trade ideas: 18

### Strong signals
- The algo is functioning as a real live selector.
- It has a coherent strategy identity:
  - BEAR_CALL_SPREAD dominates
  - BULL_PUT_SPREAD is second
- It naturally gravitates toward a realistic subset of symbols:
  - XOM, XLE, BAC, OXY, XLF, DIS, IWM, NFLX, PG
- Options-context is materially influencing decisions.

### Weak signals
- Too many suspicious surfaced trade ideas.
- Final artifact metadata is incomplete/inconsistent.
- Rejection logic is overly concentrated in:
  - `directional state is not actionable`
- Technical structure awareness appears too shallow.
- Historical review is hindered by local DB/provider mismatch.
- Outcome tracking is insufficient.

### Main conclusions
The project does **not** need a rewrite.  
It needs:
1. stronger artifact integrity
2. better technical structure modeling
3. SQLite-first data architecture
4. better score transparency
5. better outcome attribution

---

## 3) Strategic goals

### Goal A — Improve signal quality
Improve trade quality by combining:
- technical structure
- options context
- regime logic
- better strike/expiry placement

### Goal B — Improve operator trust
Every surfaced trade idea should be:
- structurally valid
- explainable
- traceable to source inputs
- reviewable later

### Goal C — Improve reproducibility
The same run should be explainable from:
- local cached data
- persisted context
- persisted feature inputs
- persisted candidate construction data

### Goal D — Improve performance review
The system should support:
- symbol-level review
- strategy-family review
- regime/context review
- realized outcome attribution

---

## 4) Guiding principles

1. Keep core logic deterministic.
2. Use LLMs only as advisory/reporting helpers, not core selectors.
3. Prefer SQLite-first local storage for reproducibility.
4. Use providers as refresh/fallback, not the only runtime data source.
5. Avoid indicator soup; prefer interpretable technical structure.
6. Keep explanation quality high for every decision.

---

## 5) Roadmap overview

The enhancement plan is split into 6 epics:

- EPIC 1 — Artifact Integrity & Run Quality
- EPIC 2 — SQLite-First Data Architecture
- EPIC 3 — Technical Analysis Enrichment
- EPIC 4 — Strategy Logic & Scoring Refinement
- EPIC 5 — Trade Construction & Validation
- EPIC 6 — Outcome Tracking & Performance Analytics

---

## 6) EPIC 1 — Artifact Integrity & Run Quality

### Objective
Make every scan artifact trustworthy and reviewable.

### Problems observed
- missing `end_date`
- missing/blank `strategy_type` in exported trade histories
- mixed live/mock/provider-quality history
- surfaced suspicious trade ideas

### Deliverables
- consistent run metadata
- trade validation flags
- run-quality labeling
- reviewable-vs-nonreviewable segmentation

### Tasks

#### 1.1 Add complete run metadata to scan results
Add/guarantee:
- `run_id`
- `end_date`
- `historical_row_provider`
- `options_provider`
- `runtime_mode`
- `run_quality`
- `is_reviewable`

**Likely files**
- `scripts/run_nightly_scan.py`
- `src/options_algo_v2/services/scan_result_builder.py`

**Acceptance criteria**
- all new scan JSONs contain the fields above
- no clean live run has null `end_date`

---

#### 1.2 Add trade-level validation metadata
Add:
- `is_structurally_valid_trade`
- `trade_validation_errors`
- `trade_validation_version`

**Likely files**
- trade idea builder
- `scan_result_builder.py`

**Acceptance criteria**
- every surfaced trade idea contains validation fields
- suspicious ideas are either blocked or explicitly tagged

---

#### 1.3 Label mock/test/degraded runs explicitly
Add:
- `is_mock`
- `is_degraded`
- `is_test_run`
- `is_reviewable`

**Acceptance criteria**
- all scans can be segmented into production-reviewable and non-reviewable

---

## 7) EPIC 2 — SQLite-First Data Architecture

### Objective
Make SQLite the primary local market-data store and provider refresh target.

### Problems observed
- daily runs appear provider-direct
- local SQLite history lagged behind live runs
- outcome review broke because DB was stale

### Target architecture
- scan reads from SQLite first
- providers refresh local DB
- providers remain available as fallback/repair sources

### Tasks

#### 2.1 Make underlying daily bars SQLite-first
Use `underlying_daily` as primary bar source.

**Likely files**
- `src/options_algo_v2/services/historical_row_provider_factory.py`
- `scripts/run_nightly_scan.py`

**Acceptance criteria**
- daily scan can run entirely from local underlying history when DB is fresh

---

#### 2.2 Make options-context snapshot SQLite-first
Persist and read options context locally before scan.

**Likely files**
- `src/options_algo_v2/services/options_context_store.py`
- `scripts/run_nightly_scan.py`

**Acceptance criteria**
- scan can consume local options context for all symbols in watchlist

---

#### 2.3 Add local chain/quote summary tables
Add tables for:
- `options_chain_snapshot_summary`
- `options_contract_quotes_daily`
- `trade_candidate_inputs`

**Acceptance criteria**
- candidate construction can be replayed from local persisted inputs

---

#### 2.4 Add freshness and staleness policy
Persist:
- last refresh timestamps
- last provider
- stale flags by table/date/symbol

**Acceptance criteria**
- scan can determine whether local data are fresh enough before execution

---

#### 2.5 Add refresh orchestrator
Create a refresh-first flow:
1. refresh underlying bars
2. refresh options context
3. refresh relevant option quotes
4. run scan from SQLite

**Likely scripts**
- `scripts/refresh_market_state_sqlite.py`
- or separate underlying/options refresh scripts

---

## 8) EPIC 3 — Technical Analysis Enrichment

### Objective
Improve directional quality, entry timing, strike safety, and structural filtering with deterministic TA.

### Why this matters
The artifact review showed:
- too much reliance on coarse directional gating
- insufficient technical timing/placement awareness
- symbol concentration in names where structure likely matters most

### Technical-analysis philosophy
Use TA to model:
- trend quality
- structure state
- support/resistance
- volatility expansion
- extension/exhaustion
- multi-timeframe alignment

Avoid indicator overload.

### Tasks

#### 3.1 Add trend quality features
Add:
- EMA 10/20/50
- EMA slope
- MA stack state
- distance to 20/50 EMA
- trend slope
- close position in recent range

**New outputs**
- `trend_direction`
- `trend_quality_score`
- `trend_extension_score`

**Likely files**
- feature builders
- `decision_engine.py`

---

#### 3.2 Add structure-state classifier
Add deterministic labels such as:
- `UPTREND_PULLBACK`
- `UPTREND_EXTENSION`
- `DOWNTREND_PULLBACK`
- `DOWNTREND_EXTENSION`
- `RANGE_BALANCED`
- `RANGE_BREAK_ATTEMPT`
- `VOLATILE_REVERSAL`
- `NON_ACTIONABLE_HARD`

**Acceptance criteria**
- current coarse directional state can be refined into structure-aware states

---

#### 3.3 Integrate support/resistance context
Add:
- nearest support/resistance
- distance to levels
- swing high/low proximity
- prior week high/low
- pivot/gap zone awareness

**Likely files**
- `src/options_algo_v2/services/support_resistance.py`
- or new `technical_context_service.py`

---

#### 3.4 Add ATR / volatility-structure metrics
Add:
- ATR(14)
- ATR as % of price
- ATR expansion/contraction state
- range expansion flags
- inside/outside day state

**Acceptance criteria**
- premium-selling logic can penalize unstable expansion regimes

---

#### 3.5 Add exhaustion/extension metrics
Add:
- RSI
- short-term ROC
- z-score from short MA
- consecutive closes
- stretch percentile

**Acceptance criteria**
- “too extended” logic becomes broader and more robust than only 20 DMA distance

---

#### 3.6 Add multi-timeframe alignment
Add daily + weekly alignment:
- trend bias
- support/resistance alignment
- structure confirmation/conflict

---

## 9) EPIC 4 — Strategy Logic & Scoring Refinement

### Objective
Reduce blunt vetoes, improve score transparency, and use TA + options context together more intelligently.

### Problems observed
- `directional state is not actionable` dominates rejections
- some options-context reasons likely act too hard
- score semantics appear mixed

### Tasks

#### 4.1 Refactor directional gating
Split current directional “not actionable” logic into:
- hard no-trade
- uncertain but tradable
- structure-conflicted
- watch-only

**Acceptance criteria**
- fewer candidates die in one coarse bucket
- richer reject reasons available for review

---

#### 4.2 Reclassify reject reasons by severity
Classify reasons as:
- `hard_invalid`
- `soft_penalty`
- `advisory_only`

Use TA as tiebreaker when options context is borderline.

---

#### 4.3 Add score decomposition
Persist:
- `signal_score`
- `technical_score`
- `options_context_score`
- `liquidity_score`
- `final_pass_score`
- `ranking_score`

**Acceptance criteria**
- surfaced trade ranking is explainable
- operator can see why a candidate passed

---

#### 4.4 Add symbol-class-specific calibration
Different thresholds for:
- broad ETFs
- sector ETFs
- mega-cap equities
- high-beta equities
- defensive equities

**Acceptance criteria**
- NFLX/TSLA/AVGO-type names use stricter structure rules than XLF/XLE-type names

---

## 10) EPIC 5 — Trade Construction & Validation

### Objective
Improve actual spread structure quality and prevent malformed surfaced trades.

### Problems observed
- suspicious live trade ideas existed
- some likely bad strike placements
- metadata around trade ideas was weak

### Tasks

#### 5.1 Add `validate_trade_idea()`
Hard validation rules:
- strategy type exists
- strike ordering consistent with strategy
- width matches strike difference
- max risk valid
- credit-width sanity valid
- no placeholder/default values

**Acceptance criteria**
- malformed trades never surface silently

---

#### 5.2 Add TA-informed strike placement
For:
- `BULL_PUT_SPREAD`
  - short strike below support + ATR buffer
- `BEAR_CALL_SPREAD`
  - short strike above resistance + ATR buffer

**Acceptance criteria**
- strike placement respects technical structure, not just delta/credit targets

---

#### 5.3 Add TA-informed expiry/width selection
Use:
- trend maturity
- ATR regime
- structure state

to influence:
- expiry choice
- width choice

---

#### 5.4 Persist candidate construction audit
Store:
- legs used
- quote inputs used
- strike-placement rationale
- validation results

---

## 11) EPIC 6 — Outcome Tracking & Performance Analytics

### Objective
Enable real strategy-performance review, not just scan-quality review.

### Problems observed
- outcome attribution was blocked by stale local DB and metadata gaps
- no clean realized outcome table exists

### Tasks

#### 6.1 Add trade outcome tables
Create tables for:
- `trade_outcome_daily`
- `trade_outcome_expiry`
- `trade_evaluation_audit`

Store:
- entry date
- entry underlying price
- expiry/last evaluation price
- short strike breach
- directionally favorable flag
- estimated outcome bucket

---

#### 6.2 Add reviewable-outcome dataset builder
Only include rows that are:
- live
- structurally valid
- reviewable
- fully attributed

---

#### 6.3 Add performance slices
Slice results by:
- strategy family
- symbol
- sector
- regime
- structure state
- options-context confidence
- TA buckets

---

#### 6.4 Add OpenClaw daily/weekly review reports
Include:
- pass/fail summary
- suspicious idea count
- symbol concentration
- TA/context explanations
- strategy-family summary
- outcome drift once available

---

## 12) Proposed implementation order

### Phase 1 — Trust and reproducibility
1. EPIC 1 artifact integrity
2. EPIC 2 SQLite-first bars/context
3. EPIC 5 trade validation

### Phase 2 — Better decision quality
4. EPIC 3 technical-analysis enrichment
5. EPIC 4 strategy/scoring refinement

### Phase 3 — Performance science
6. EPIC 6 outcome tracking and analytics

---

## 13) Immediate top-priority tasks

If only a handful of changes can be done first, prioritize:

1. Add `validate_trade_idea()`
2. Guarantee `end_date` + provider + strategy fields in artifacts
3. Make underlying history SQLite-first
4. Add support/resistance-aware strike placement
5. Refine directional-state classification with trend quality
6. Add ATR/range-expansion penalties
7. Add score decomposition
8. Add outcome tracking tables

---

## 14) Suggested Milestones

### Milestone 1 — Artifact trust
- EPIC 1 complete
- suspicious trade leakage reduced to near-zero

### Milestone 2 — SQLite-first runtime
- EPIC 2 complete
- daily scan reads local DB by default

### Milestone 3 — Technical structure v1
- EPIC 3 complete
- structure-aware states active

### Milestone 4 — Scoring/decision refinement
- EPIC 4 complete
- hard/soft/advisory reason framework in place

### Milestone 5 — Outcome review
- EPIC 6 complete
- reviewable performance dashboard available

---

## 15) Definition of Done (project-level)

The enhancement effort is considered successful when:

1. production scans are fully reviewable and reproducible
2. surfaced trade ideas are structurally validated
3. technical structure meaningfully improves entry/placement logic
4. scans run from SQLite-first local data by default
5. live outcome review is possible from persisted local data
6. operator reports clearly explain why trades passed or failed

---

## 16) Open questions

1. How much raw options-chain detail should be stored locally vs summarized?
2. Should multi-timeframe weekly features be added in the main daily scan or precomputed?
3. Which provider should be canonical for underlying outcome attribution in SQLite refresh flows?
4. Should support/resistance be level-based only, or include volume-profile/pivot logic?
5. Which symbol classes should get custom TA thresholds first?

---

## 17) Recommended next document

After this plan is committed, create:
- `docs/IMPLEMENTATION_TRACKER.md`

with:
- epic
- issue link
- status
- owner
- target date
- blockers
- notes

This will make progress visible inside the repo even before all GitHub issues are opened.

