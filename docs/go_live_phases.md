# Go-Live Phases

## Current State (as of 2026-03-22)

All early foundation phases are complete. The platform runs a watchlist-driven paper-live pipeline with real Databento bars, real Polygon options chain, real IV/HV ratio, config-driven spread selection, options context scoring, and persistent validation logging.

**Completed work:**
- 58-symbol universe across all 11 GICS sectors
- Live Databento bars → real SMA/ATR/ADX/RSI/HV20
- Live Polygon options chain normalization
- Real `iv_hv_ratio`
- Options context snapshot (PCR, skew, expected move, chain confidence)
- Options context score adjustment and hard-reject
- Watchlist-driven scans (build → options-viability → filter → run)
- Config-driven spread selection (BULL strategies)
- Spread scoring model (delta fit, liquidity, efficiency)
- Explainable scan artifacts with per-symbol feature debug and decision trace
- Paper-live daily run flow with JSONL/CSV validation logging
- Review scripts and leaderboard tooling
- Strict-live blocking for placeholder or degraded inputs
- Paper-live + SQLite analytics validation loop operational

---

## Phase 1 — Complete IV Rank (current priority)

**Goal:** Make `iv_rank` real for all symbols so IV state classification uses actual historical percentile rank instead of the 50.0 placeholder.

**Tasks:**
1. Wire `append_iv_proxy_observation` into `run_nightly_scan.py` — called once per symbol per live run after IV proxy is estimated
2. Run daily until 60 observations per symbol exist
3. Monitor `iv_rank_ready_symbols` in scan metadata
4. Verify IV state changes when rank is real

**Exit criteria:**
- `iv_rank_ready_symbols` includes all active watchlist symbols
- `iv_rank_insufficient_history_symbols` is empty for active symbols
- No placeholder IV rank in live scan metadata

---

## Phase 2 — Bear Spread Construction

**Goal:** Close the gap where BEAR_CALL_SPREAD and BEAR_PUT_SPREAD signals qualify correctly but produce zero trade candidates.

**Tasks:**
1. Add `BEAR_CALL_SPREAD` and `BEAR_PUT_SPREAD` handling to `expiration_aware_spread_selector.py`
2. Add corresponding scoring functions (`score_bear_call_spread`, `score_bear_put_spread`) in `spread_scoring.py`
3. Confirm bear spread candidates appear in artifacts when directional state is bearish

**Exit criteria:**
- Bear-regime signals produce trade candidates end-to-end
- Spread scoring model covers all four strategy types

---

## Phase 3 — Scoring and Signal Quality Improvements

**Goal:** Make candidate scoring reflect actual signal strength rather than all qualified candidates scoring 100.0 flat.

**Tasks:**
1. Pass `adx`, `iv_ratio`, and `breadth_distance` to `score_candidate` in `decision_engine.py`
2. Populate `iv_rv_spread` (IV proxy minus HV20) in `feature_normalizer.py` so the third IV-rich signal activates
3. Wire `expected_move.py` into trade candidate filtering or scoring
4. Wire `support_resistance.py` into spread strike validation
5. Wire `regime_transition.py` into entry timing or scoring adjustments

**Exit criteria:**
- Qualified candidates score differently based on ADX strength, IV ratio, and breadth distance
- IV_RICH classification can be triggered by any two of the three available signals
- Expected move edge classification is used in candidate evaluation

---

## Phase 4 — Production Hardening

**Goal:** Make the pipeline safe for unattended strict-live operation.

**Tasks:**
1. Breadth freshness checks — reject if market breadth data is stale
2. Quote-quality thresholds — define and enforce minimum chain quality standards
3. Risk cap enforcement — per-trade, per-sector, portfolio-level
4. Monitoring hooks — structured failure logging, degraded-mode alerting
5. Strict-live readiness checklist — explicit go/no-go criteria

**Exit criteria:**
- Zero placeholder inputs in live scan
- All data freshness and quality checks pass automatically
- Strict-live runs cleanly on a full watchlist without manual intervention

---

## Phase 5 — Strict-Live Gate

**Goal:** Formally certify the system for unattended strict-live operation.

**Readiness checklist:**
- [ ] `iv_rank` real for all active symbols (no placeholder fallback)
- [ ] Bear spread construction working
- [ ] Continuous scoring inputs wired
- [ ] Production hardening complete
- [ ] Multiple consecutive strict-live runs clean
- [ ] Quote-quality diagnostics passing
- [ ] Risk caps enforced

**Exit criteria:**
- All checklist items green
- System runs strict-live daily without intervention

---

## Phase 6 — Paper Execution Simulation

**Goal:** Add realistic paper execution tracking before any capital is risked.

**Tasks:**
1. Paper execution path with fill/slippage assumptions
2. Per-trade entry/exit detail logging
3. Daily execution summary (fill rate, slippage, no-fill events)
4. Paper P&L tracking with max-risk accounting

**Exit criteria:**
- Stable paper execution results across multiple sessions
- Fill rate and slippage assumptions validated against live chain data

---

## Phase 7 — Small-Capital Live Deployment

**Goal:** Controlled live deployment with minimal capital.

**Constraints:**
- Small position sizes
- Maximum 1–2 trades per day
- Strict risk caps (1% max risk per trade)
- Optional manual approval per trade
- Full post-trade review

**Exit criteria:**
- Stable live operations over multiple weeks
- Clean post-trade review with no surprise fills or assignment events

---

## Daily operating loop (current)

```bash
set -a; source .env; set +a

PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json

python3 scripts/review_scan_analytics_sqlite.py --limit-runs 20 --symbols BAC NFLX CRM

```
