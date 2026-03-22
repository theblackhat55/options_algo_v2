# options_algo_v2

A watchlist-driven options strategy platform that scans underlyings, evaluates market/technical/volatility context, selects spread candidates, and produces explainable trade ideas.

The project operates in **paper-live mode with real market data inputs**. A strict-live mode is implemented and intentionally blocks runs when placeholder or degraded inputs remain.

---

## What this repo does

The pipeline runs left-to-right in this order:

1. **Universe / watchlist input** — 58-symbol universe across all 11 GICS sectors (`config/universe_v1.yaml`)
2. **Historical bar features** — Databento daily OHLCV → `close`, `dma20`, `dma50`, `atr20`, `adx14`, `rsi14`, `hv20`
3. **Market breadth + regime** — live breadth provider, dead zone 48–52%
4. **Options chain** — Polygon live snapshots, normalized to `bid/ask/mid/delta/OI/volume/IV`
5. **Volatility context**
   - `iv_hv_ratio` — near-ATM IV proxy / HV20 from bars (live)
   - `iv_rank` — percentile rank over rolling window; auto-accumulated each live scan run via `upsert_iv_proxy_rows`
6. **Market regime classifier** — TREND_UP / TREND_DOWN / RANGE_UNCLEAR / RISK_OFF
7. **Directional state classifier** — BULLISH_CONTINUATION / BULLISH_BREAKOUT / BEARISH_CONTINUATION / BEARISH_BREAKDOWN / NEUTRAL / NO_TRADE
8. **IV state classifier** — IV_RICH (2-of-3 signals: rank ≥ 60, IV/HV ≥ 1.25, IV-RV spread ≥ 5) / IV_CHEAP (1 signal) / IV_NORMAL
9. **Strategy selector** — maps regime × directional state × IV state → BULL_PUT_SPREAD / BULL_CALL_SPREAD / BEAR_CALL_SPREAD / BEAR_PUT_SPREAD
10. **Hard filters** — event (earnings window), liquidity, extension (2×ATR from DMA20)
11. **Candidate scoring** — 0–100 points: regime fit (20), directional fit (25), IV fit (20), liquidity (20), expected move (15); extension penalty −10
12. **Options context layer** — confidence score, PCR, skew, expected move from Polygon chain; adjusts final score and flags untradeable chains
13. **Spread selection** — config-driven DTE/delta bands from `strategy_v1.yaml`, spread scoring model (delta fit, liquidity, efficiency)
14. **Trade idea generation + artifact writing**
15. **Paper-live validation logging**

---

## Current status

### Working now (verified from code)
- Live Databento daily bars → real SMA/ATR/ADX/RSI/HV20
- Live Polygon options chain normalization
- Real `iv_hv_ratio` (near-ATM IV proxy ÷ HV20)
- Options context snapshot (PCR, skew, expected move, chain confidence)
- Options context adjustment to candidate score (confidence, regime, PCR, skew)
- 58-symbol universe across all 11 GICS sectors
- Watchlist-driven scans
- Config-driven spread selection (DTE/delta bands from `strategy_v1.yaml`)
- Spread scoring model (delta fit, liquidity, efficiency)
- Explainable scan artifacts with per-symbol feature debug and decision trace
- Paper-live daily run flow with JSONL/CSV validation logging
- Review scripts (`review_paper_live_logs.py`, `paper_live_symbol_leaderboard.py`)
- Strict-live blocking when placeholder IV inputs are present
- 280 tests passing

### Known gaps (code-confirmed)
- **`iv_rank` threshold lowered to 20 observations** — `upsert_iv_proxy_rows` is now called automatically on every live scan run; history accumulates daily. IV rank becomes active once 20 observations per symbol exist (previously 60).
- **`support_resistance.py` not called from main scan** — wired into `best_trade_candidate_selector.py` and `trade_candidate_serializer.py` but not invoked from `run_nightly_scan.py` or `decision_engine.py` directly.

### Operational posture
This repo is best treated today as a **paper-live validated signal platform**. Paper-live monitoring, watchlist scans, artifact inspection, and validation logging are all safe. Unattended strict-live or live deployment is not yet appropriate.

---

## Repository layout

### Config
- `config/strategy_v1.yaml` — DTE bands, delta bands, breadth thresholds, IV rank min observations, extension ATR multiple, scoring thresholds
- `config/universe_v1.yaml` — 58-symbol universe (all 11 GICS sectors)
- `config/risk_v1.yaml` — min price/volume/OI, max bid-ask spread, quote age, risk per trade, max positions, sector concentration

### Core services (`src/options_algo_v2/services/`)
| File | Purpose |
|---|---|
| `feature_normalizer.py` | Delegates to canonical classifiers, builds `PipelineEvaluationPayload` |
| `decision_engine.py` | Strategy selector → hard filters → score → `CandidateDecision` |
| `candidate_ranker.py` | `score_candidate` — 100-pt boolean/continuous blend |
| `options_context_decision_adjuster.py` | Applies chain confidence/PCR/skew score delta, hard-rejects untradeable chains |
| `trade_candidate_ranking.py` | Spread scoring model (delta fit, liquidity, efficiency) + context adjustment |
| `spread_scoring.py` | `score_bull_put_spread` / `score_bull_call_spread` internals |
| `expiration_aware_spread_selector.py` | Config-driven spread selection across all four spread families |
| `iv_rank_history.py` | `compute_iv_rank_from_history`, `append_iv_proxy_observation` |
| `iv_feature_estimator.py` | `compute_iv_hv_ratio_from_snapshot_and_bars`, `estimate_near_atm_implied_vol` |
| `options_context_service.py` | Chain quality, expected move, positioning, skew, confidence scoring |
| `support_resistance.py` | Pivot-point S/R detection and strike validation (wired into trade candidate selector) |
| `expected_move.py` | Implied vs. forecast expected move edge classification (wired into `feature_normalizer.py`) |
| `regime_transition.py` | Regime transition detection and confidence tracking (wired into `run_nightly_scan.py`) |
| `mock_historical_rows.py` | Calibrated mock series: pass (BULLISH_CONTINUATION), extended (NO_TRADE), neutral |

### Key scripts (`scripts/`)
- `run_nightly_scan.py` — core scan entry point
- `run_trade_ideas.py` — scan + print trade ideas
- `run_paper_live_daily.py` — scan + append validation logs
- `run_strict_live_scan.py` — scan with strict-live mode enforced
- `run_sample_scan.py` — quick scan against mock series (no API keys required)
- `inspect_scan_debug.py` — per-symbol feature/decision inspector
- `inspect_scan_result.py` — raw scan artifact inspector
- `review_paper_live_logs.py` — multi-run pass rate / rejection review
- `paper_live_symbol_leaderboard.py` — per-symbol pass frequency / ADX / IV-HV profile
- `build_watchlist.py`, `filter_options_watchlist.py`, `build_options_watchlist.py`
- `build_options_context_snapshot.py` — compute and persist options context for a watchlist
- `show_databento_runtime_info.py` — inspect Databento API connectivity and bar availability
- `debug_polygon_chain_payload.py` — inspect raw Polygon chain response for a symbol
- `test_live_historical_rows.py`, `test_live_options_chain.py` — connectivity smoke tests

### Output directories
- `data/scan_results/` — scan artifacts (`scan_<run_id>.json`)
- `data/watchlists/` — watchlist JSON files
- `data/validation/` — paper-live JSONL/CSV logs
- `data/cache/` — `market_history_watchlist60.db` (SQLite — IV proxy history, options context)

---

## Quick start

### 1. Activate environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Load environment variables
```bash
set -a
source .env
set +a
```

Minimum required for live mode:
```
OPTIONS_ALGO_RUNTIME_MODE=live
DATABENTO_API_KEY=...
POLYGON_API_KEY=...
```

### 3. Run a paper-live scan
```bash
PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

### 4. Review results
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5
```

### 5. Inspect a scan artifact
```bash
python - <<'PY'
from pathlib import Path
files = sorted(Path("data/scan_results").glob("scan_*.json"))
print(files[-1] if files else "no scan files found")
PY

PYTHONPATH=src python scripts/inspect_scan_debug.py data/scan_results/<scan_file>.json
```

For a shorter daily operator guide, see [`docs/OPERATOR_QUICKSTART.md`](docs/OPERATOR_QUICKSTART.md).

---

## Example workflows

### Run trade ideas directly
```bash
PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

Output includes: scan summary, rejection reason counts, strategy type counts, top trade candidates ranked by spread scoring model, trade ideas if candidates pass.

### Strict-live readiness check
```bash
OPTIONS_ALGO_STRICT_LIVE_MODE=1 \
PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

Expected to fail while `iv_rank` placeholder inputs remain. That is the intended behavior.

### Daily paper-live loop
```bash
set -a; source .env; set +a

PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json

PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5
```

---

## Strategy logic

### Regime permissions
| Regime | Allowed structures |
|---|---|
| TREND_UP | BULL_PUT_SPREAD, BULL_CALL_SPREAD |
| TREND_DOWN | BEAR_CALL_SPREAD, BEAR_PUT_SPREAD |
| RANGE_UNCLEAR | BULL_PUT_SPREAD, BEAR_CALL_SPREAD, BEAR_PUT_SPREAD |
| RISK_OFF | none |
| SYSTEM_DEGRADED | none |

### Strategy selection by IV state
| Directional state | IV_RICH | IV_NORMAL / IV_CHEAP |
|---|---|---|
| Bullish (any) | BULL_PUT_SPREAD | BULL_CALL_SPREAD |
| Bearish (any) | BEAR_CALL_SPREAD | BEAR_PUT_SPREAD |

### Hard filter thresholds (from `risk_v1.yaml`)
- Min underlying price: $20
- Min avg daily volume: 1,000,000
- Min option OI: 250
- Min option volume: 50
- Max bid-ask spread: 8% of mid
- Max option quote age: 60 s
- Max underlying quote age: 10 s
- Min candidate score: 70

### Key strategy parameters (from `strategy_v1.yaml`)
- Credit spread DTE: min 25, target 35, max 45
- Debit spread DTE: min 14, target 28, max 45
- Credit short delta: 0.15–0.30 (target 0.22)
- Debit long delta: 0.45–0.65 (target 0.55)
- Breadth thresholds: bullish > 52%, bearish < 48%
- ADX trending minimum: 18
- Extension ATR multiple: 2.0
- IV rank lookback: 60 observations

---

## Volatility features

### `iv_hv_ratio` — live
- Implied vol proxy: average IV of 4 nearest-ATM liquid Polygon contracts
- Historical vol: 20-day annualized log-return stdev from Databento bars
- Ratio: `iv_proxy / hv20`

### `iv_rank` — accumulating
- Percentile rank: `(current_iv - min) / (max - min) × 100` over trailing observations
- `upsert_iv_proxy_rows` called automatically every live scan run via `history_store`
- Falls back to placeholder (50.0) when fewer than 20 observations exist per symbol
- History storage: SQLite (`data/cache/market_history_watchlist60.db`, table `iv_proxy_daily`)

### IV state signals active today
- `iv_rank` signal: active when history ≥ 20 obs per symbol; otherwise fallback = 50.0
- `iv_hv_ratio` signal: always active (live)
- `iv_rv_spread` signal: computed as `(iv_hv_ratio - 1.0) × 100`; active when `iv_hv_ratio` is available

---

## Strict-live behavior

Strict-live mode (`OPTIONS_ALGO_STRICT_LIVE_MODE=1`) blocks runs if:
- placeholder IV rank inputs are in use
- placeholder IV/HV ratio inputs are in use
- placeholder liquidity inputs are in use

This is intentional. Treat strict-live failure as a safety gate, not a bug.

---

## Validation tooling

### Daily outputs
- `data/validation/paper_live_runs.jsonl` — run-level summary
- `data/validation/paper_live_symbol_decisions.jsonl` — per-symbol decision detail
- `data/validation/paper_live_runs.csv` — tabular run summary

### What to watch daily
- passed count per run
- repeated passing symbols
- `directional state is not actionable` frequency
- `options_context_missing` frequency
- whether `iv_rank_ready_symbols` is growing
- score distribution across candidates

---

## Development

```bash
pytest                  # 280 tests, all passing
ruff check .            # lint
mypy src                # type check
```

---

## Next milestones

1. **Wire `support_resistance.py` into `run_nightly_scan.py`** for strike-level S/R validation at scan time
2. **Complete production hardening** — breadth freshness checks, quote-quality thresholds, risk caps, monitoring
3. **Enable strict-live** once IV rank history reaches threshold across the full watchlist
4. **Expand paper-live validation** — accumulate multi-week pass rate, tune scoring thresholds from real signal data
5. **Add paper execution simulation** — fill/slippage model, daily P&L tracking against trade ideas

---

## Documentation
- [`docs/RUNBOOK.md`](docs/RUNBOOK.md) — full operational runbook
- [`docs/OPERATOR_QUICKSTART.md`](docs/OPERATOR_QUICKSTART.md) — short daily operator guide
- [`docs/live_status_summary.md`](docs/live_status_summary.md) — current pipeline status and known gaps
- [`docs/go_live_phases.md`](docs/go_live_phases.md) — phased plan to strict-live and beyond
- [`docs/watchlist_design.md`](docs/watchlist_design.md) — watchlist architecture and current implementation
- [`docs/options_watchlist_policy.md`](docs/options_watchlist_policy.md) — options viability policy
- [`docs/rulebook.md`](docs/rulebook.md) — deterministic trading rules specification (with implementation gap notes)
- [`docs/strategy.md`](docs/strategy.md) — strategy philosophy and decision layers
- [`docs/execution.md`](docs/execution.md) — execution policy spec (future)
- [`docs/simulation.md`](docs/simulation.md) — simulation and backtest assumptions (future)
- [`docs/dashboard_integration.md`](docs/dashboard_integration.md) — artifact schema for dashboard consumers
- [`docs/vision.md`](docs/vision.md) — long-term platform vision
