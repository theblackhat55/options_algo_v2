# Go-Live Plan (Phased)

## Current State
- Databento historical daily bars working in strict live
- Polygon live options chain working
- Strict live runner completes successfully
- Current universe too small (10 symbols)
- Need broader market scan + watchlist builder before options strategy execution at scale

---

## Phase A — Explainability + Watchlist Foundation
### Goals
- Make decisions auditable
- Prepare broader market scanning
- Introduce watchlist-first architecture

### Deliverables
1. Add feature-level debug traces to scan artifact
2. Add decision-trace metadata to scan artifact
3. Add Polygon quote-quality counters
4. Add watchlist builder skeleton
5. Add broader-universe input support

### Exit Criteria
- Every symbol decision is explainable
- A watchlist file can be generated from a broader underlying universe

---

## Phase B — Broad Market Underlying Scan
### Goals
- Scan a larger liquid universe
- Rank symbols before options-chain evaluation

### Universe
- Start with S&P 500 + major ETFs + liquid optionable names
- Expand later to broader optionable universe

### Underlying Filters
- minimum price
- minimum average dollar volume
- trend strength
- momentum / directional setup
- volatility suitability
- breadth alignment

### Exit Criteria
- Broad universe reduced to manageable candidate list
- Watchlist saved to JSON (and later Parquet)

---

## Phase C — Options Viability Watchlist
### Goals
- Filter watchlist to symbols whose options are actually tradeable

### Options Viability Checks
- options volume
- open interest
- bid/ask width
- number of viable contracts near target DTE
- real quote presence
- greek completeness (or sparse-greek warnings)

### Exit Criteria
- Tradeable-options watchlist produced
- Weak options names excluded before full v2 strategy scan

---

## Phase D — Run v2 Algo on Watchlist
### Goals
- Replace 10-symbol fixed scan with watchlist-driven scan

### Deliverables
- run_nightly_scan supports watchlist input
- run_trade_ideas supports --watchlist path
- strict live scan runs on watchlist symbols

### Exit Criteria
- v2 algo consumes watchlist-generated symbol set

---

## Phase E — Strategy Calibration
### Goals
- Validate behavior over multiple live sessions

### Tasks
- Run strict live daily
- Archive artifacts
- Review pass rates, rejection reasons, trade counts
- Tune thresholds if strategy is too strict or too noisy

### Exit Criteria
- Trade frequency and selectivity understood
- No-trade days acceptable and explainable

---

## Phase F — Production Hardening
### Goals
- Make strict live safe for production

### Deliverables
- degraded-data policy
- strict quote-quality policy
- breadth freshness checks
- risk caps
- no-trade on stale/missing data
- monitoring and alerts

### Exit Criteria
- Strategy and data controls are enforced automatically

---

## Phase G — Paper Live
### Goals
- Simulate execution before real capital

### Deliverables
- paper execution path
- fill/slippage assumptions
- daily paper results
- operator review

### Exit Criteria
- Stable paper results over multiple sessions

---

## Phase H — Small-Capital Go Live
### Goals
- Controlled live deployment

### Constraints
- small size
- few trades per day
- strict risk caps
- no synthetic-quote-dependent trades
- manual approval optional

### Exit Criteria
- Stable live operations
- Clean post-trade review
