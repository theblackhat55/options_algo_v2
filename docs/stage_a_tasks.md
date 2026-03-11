# Stage A Tasks

## Objective
Add explainability and lay the foundation for broader watchlist-based scanning.

---

## Task 1 — Feature Trace in Scan Artifact
Add per-symbol feature debug data:
- close
- price_vs_20dma_pct
- adx14
- iv_rank
- iv_hv_ratio
- avg_daily_volume
- breadth input

### Status
Pending

---

## Task 2 — Decision Trace in Artifact
Add per-symbol rule trace:
- market_regime
- directional_state
- iv_state
- extension filter result
- liquidity filter result
- final rejection reasons

### Status
Pending

---

## Task 3 — Polygon Quote Quality Metadata
Add:
- total quotes fetched
- quotes with real last_quote
- synthetic quote count
- missing greeks count
- zero delta count
- zero OI count

### Status
Pending

---

## Task 4 — Broader Universe Loader
Support:
- default universe file
- custom symbol file
- watchlist file
- explicit symbols from CLI

### Status
Pending

---

## Task 5 — Watchlist Builder Skeleton
Create:
- scripts/build_watchlist.py
- watchlist artifact output
- initial ranking fields

### Status
Pending

---

## Task 6 — Universe Expansion Strategy
Start from:
- S&P 500
- major ETFs
- liquid optionable names

Avoid going directly to all listed tickers on day 1.

### Status
Pending

---

## Exit Criteria
- Explainability added
- Watchlist skeleton exists
- Broader-universe scan path exists
