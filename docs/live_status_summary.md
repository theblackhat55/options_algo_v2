# Live Pipeline Status Summary

## Overview
The options algorithm has progressed from partially mocked evaluation to a working **paper-live pipeline** with real market structure inputs, live scan diagnostics, and persistent validation logging.

The system now runs end-to-end in live mode, produces explainable scan artifacts, generates trade candidates and trade ideas, and records daily validation outputs for later review.

---

## What is now live / real

### Historical market data
- **Databento daily bars** are used in live mode
- Real underlying features are computed from bars:
  - `close`
  - `dma20`
  - `dma50`
  - `atr20`
  - `adx14`

### Market breadth
- Live market breadth provider is wired
- Breadth override handling is supported and surfaced in runtime metadata

### Options chain / options selection
- **Polygon live options chain snapshots** are used
- Option quote normalization includes:
  - bid / ask / mid
  - delta
  - open interest
  - volume
  - implied volatility
- Spread selection and leg orientation were corrected
- Trade ideas now contain correct option symbols / strikes in CLI output

### Volatility features
- **`iv_hv_ratio` is now real**
  - implied-vol proxy is derived from near-ATM Polygon chain contracts
  - historical volatility is derived from Databento daily bars using log returns
- **IV proxy history persistence is now implemented**
  - stored at `data/state/iv_proxy_history.jsonl`
- **First-pass `iv_rank` infrastructure exists**
  - current implied-vol proxy is persisted daily
  - rolling `iv_rank` will become real once enough history accumulates

### Scan diagnostics / transparency
- Scan artifacts expose:
  - feature debug by symbol
  - decision trace by symbol
  - raw directional inputs
  - directional checks
  - rejection reasons
- `scripts/inspect_scan_debug.py` can inspect per-symbol evaluation details

### Paper-live validation tooling
- Daily paper-live runner added
- Logging outputs added:
  - `data/validation/paper_live_runs.jsonl`
  - `data/validation/paper_live_symbol_decisions.jsonl`
  - `data/validation/paper_live_runs.csv`
- Review tooling added:
  - `scripts/review_paper_live_logs.py`
  - `scripts/paper_live_symbol_leaderboard.py`

---

## What remains placeholder / degraded

### `iv_rank`
- `iv_rank` is still placeholder until enough distinct daily IV proxy observations accumulate
- Runtime metadata now explicitly shows:
  - `iv_rank_ready_symbols`
  - `iv_rank_insufficient_history_symbols`
  - `iv_rank_history_path`
  - `iv_rank_trailing_observations`

### Strict-live behavior
- **Strict-live mode correctly fails** if placeholder IV inputs are still present
- At present, strict-live remains blocked because `iv_rank` is not yet fully real

---

## Current paper-live behavior

Recent paper-live runs show:

- the pipeline is stable and repeatable
- one consistently qualifying symbol has emerged: **XLE**
- current pass rate on the filtered 10-symbol watchlist is approximately **10%**
- most rejections are now due to **real directional-state logic**, not broken plumbing

Observed patterns:
- **XLE**: consistently passes with bullish continuation / rich IV profile
- **AMD / AMZN / CRM / NFLX / NVDA / SMH**: often rejected as `NEUTRAL`
- **JPM / TSLA / UBER**: often rejected as bearish continuation in an up regime

This suggests the system is now producing **sparse but explainable** signals rather than failing because of placeholder feature inputs.

---

## Current operational assessment

### Ready
- paper-live monitoring
- daily validation logging
- multi-run review / leaderboard analysis
- continued live signal observation

### Not yet ready
- unattended strict-live / production execution
- full strict-live approval, because `iv_rank` is not yet fully real

---

## Recommended next steps

1. **Keep daily paper-live runs going**
   - allow IV proxy history to accumulate
   - monitor when symbols begin moving into `iv_rank_ready_symbols`

2. **Continue reviewing multi-run logs**
   - pass frequency
   - repeated winners / rejects
   - directional-state distribution
   - strategy-family mix

3. **Reassess after IV rank history matures**
   - once enough observations exist, `iv_rank` can stop falling back
   - then re-evaluate strict-live readiness

4. **Only then consider threshold tuning**
   - avoid overfitting before more live observations accumulate

---

## Suggested short GitHub note

Implemented a working paper-live options scan pipeline with real Databento bars, real ADX, real Polygon-derived IV/HV ratio, corrected spread construction, detailed scan diagnostics, and persistent paper-live validation logging/review tooling.

Strict-live remains intentionally blocked because IV rank is still in a history-building phase. IV proxy history is now persisted and readiness metadata is exposed so the system can transition off placeholder IV rank once enough daily observations accumulate.
