# Live Pipeline Status Summary

## Current State (as of 2026-03-22)

The platform runs a fully functional **paper-live pipeline** with real market data, explainable scan artifacts, spread selection, trade idea generation, and persistent validation logging.

---

## What is live and working

### Historical market data
- **Databento daily bars** in live mode
- Real computed features: `close`, `dma20`, `dma50`, `atr20`, `adx14`, `rsi14`, `hv20`

### Market breadth
- Live market breadth provider wired into regime classifier
- Breadth override flag surfaced in runtime metadata when override is active

### Options chain
- **Polygon live options chain snapshots**
- Quote normalization: bid / ask / mid / delta / open interest / volume / IV
- Options context snapshot: PCR, skew, expected move (1d/1w/30d), chain confidence
- Options context score adjustment and hard-reject for untradeable chains

### Volatility features
- **`iv_hv_ratio` is real** — near-ATM Polygon IV proxy ÷ HV20 from Databento bars
- **`iv_rank` infrastructure exists** — percentile rank over 60-observation rolling window; stays at placeholder (50.0) until 60 observations per symbol accumulate
- History stored at `data/state/iv_proxy_history.jsonl`

### Classifiers and decision logic
- Market regime: TREND_UP / TREND_DOWN / RANGE_UNCLEAR (RISK_OFF unreachable — `vix_defensive` hardwired False)
- Directional state: BULLISH_CONTINUATION / BULLISH_BREAKOUT / BEARISH_CONTINUATION / BEARISH_BREAKDOWN / NEUTRAL / NO_TRADE
- IV state: IV_RICH (2 active signals: `iv_rank ≥ 60` AND `iv_hv_ratio ≥ 1.25`) / IV_CHEAP / IV_NORMAL
- Strategy selector: maps regime × directional × IV → spread type
- Hard filters: event (earnings window), liquidity, extension (2×ATR from DMA20)
- Candidate scoring: 100-pt model; all qualified candidates currently score 100.0 flat before options context adjustment (continuous ADX/IV/breadth inputs not yet passed to `score_candidate`)

### Spread selection and trade ideas
- Config-driven DTE/delta bands from `strategy_v1.yaml`
- Spread scoring model (delta fit, liquidity, efficiency) for BULL_PUT_SPREAD and BULL_CALL_SPREAD
- Trade idea generation and scan artifact writing
- **Bear spread construction not yet wired** — BEAR_CALL_SPREAD and BEAR_PUT_SPREAD signals qualify correctly but `expiration_aware_spread_selector.py` returns empty candidates for both

### Paper-live validation tooling
- `scripts/run_paper_live_daily.py` — daily scan with validation log append
- `data/validation/paper_live_runs.jsonl`, `paper_live_symbol_decisions.jsonl`, `paper_live_runs.csv`
- `scripts/review_paper_live_logs.py` — multi-run pass rate, rejection reasons
- `scripts/paper_live_symbol_leaderboard.py` — per-symbol pass frequency, ADX, IV/HV

### Testing
- 280 tests passing

---

## Known gaps (code-confirmed)

| Gap | Location | Impact |
|---|---|---|
| `iv_rank` not auto-accumulating | `run_nightly_scan.py` imports but never calls `append_iv_proxy_observation` | IV rank stays placeholder until 60 obs/symbol exist |
| Bear spread construction missing | `expiration_aware_spread_selector.py` handles BULL strategies only | Bear-regime signals produce zero trade candidates |
| `iv_rv_spread` always None | `feature_normalizer.py` passes `iv_rv_spread=None` | Third IV-rich signal inactive; IV_RICH needs both rank ≥ 60 AND iv_hv ≥ 1.25 |
| Continuous scoring not used | `decision_engine.py` passes booleans only to `score_candidate` | All qualified candidates score 100.0 flat before context adjustment |
| `vix_defensive` hardwired False | `feature_normalizer.py` | RISK_OFF regime unreachable |

---

## Strict-live status

Strict-live (`OPTIONS_ALGO_STRICT_LIVE_MODE=1`) is intentionally blocked while placeholder `iv_rank` inputs remain. This is a safety gate. Until `append_iv_proxy_observation` is wired into the scan loop and 60 observations per symbol accumulate, strict-live will not pass.

---

## Operational assessment

### Safe now
- Daily paper-live monitoring
- Scan artifact inspection
- Validation log review and leaderboard analysis
- Watchlist experimentation
- IV history accumulation

### Not yet safe
- Unattended strict-live execution
- Bear-regime signal-to-trade pipeline (spread construction missing)
- Small-capital live deployment

---

## Near-term priorities

1. Wire `append_iv_proxy_observation` into `run_nightly_scan.py` so IV proxy history auto-accumulates every live run
2. Add bear spread construction to `expiration_aware_spread_selector.py`
3. Pass continuous ADX/IV/breadth inputs to `score_candidate` in `decision_engine.py`
4. Populate `iv_rv_spread` (IV proxy minus HV20) so the third IV signal activates
5. Wire `expected_move.py`, `support_resistance.py`, and `regime_transition.py` into the main pipeline
6. Complete production hardening (breadth freshness, quote-quality thresholds, risk caps)
7. Enable strict-live after placeholder IV rank is eliminated
