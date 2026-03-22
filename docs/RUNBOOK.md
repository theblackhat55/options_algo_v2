# RUNBOOK

## Purpose
This runbook explains how to operate the `options_algo_v2` platform end-to-end: environment setup, daily paper-live runs, diagnostics, validation review, and strict-live readiness checks.

For a shorter daily reference, see [`OPERATOR_QUICKSTART.md`](OPERATOR_QUICKSTART.md).

---

# 1. Platform Overview

## Pipeline flow (left to right)

1. **Universe / watchlist input** — 58-symbol universe (`config/universe_v1.yaml`) or a filtered watchlist JSON
2. **Historical bars** — Databento daily OHLCV → `close`, `dma20`, `dma50`, `atr20`, `adx14`, `rsi14`, `hv20`
3. **Market breadth + regime** — live breadth provider, dead zone 48–52%
4. **Options chain** — Polygon live snapshots (bid/ask/mid/delta/OI/volume/IV)
5. **Volatility context**
   - `iv_hv_ratio` — near-ATM IV proxy ÷ HV20 (live)
   - `iv_rank` — percentile rank over 60-observation rolling window (placeholder until history accumulates)
6. **Market regime classifier** — TREND_UP / TREND_DOWN / RANGE_UNCLEAR / RISK_OFF
7. **Directional state classifier** — BULLISH_CONTINUATION / BULLISH_BREAKOUT / BEARISH_CONTINUATION / BEARISH_BREAKDOWN / NEUTRAL / NO_TRADE
8. **IV state classifier** — IV_RICH (2-of-2 active signals: `iv_rank ≥ 60` + `iv_hv_ratio ≥ 1.25`) / IV_CHEAP / IV_NORMAL
9. **Strategy selector** — regime × directional × IV → spread type
10. **Hard filters** — event (earnings inside holding window), liquidity, extension (2×ATR from DMA20)
11. **Candidate score** — 100-pt: regime 20 + directional 25 + IV 20 + liquidity 20 + expected move 15; −10 if extended
12. **Options context layer** — chain confidence, PCR, skew, expected move adjust score; untradeable chains hard-reject
13. **Spread selection** — config-driven DTE/delta bands, spread scoring model (delta fit, liquidity, efficiency)
14. **Trade idea generation + scan artifact**
15. **Paper-live validation logging**

## Analytical modules (implemented, not yet wired into main pipeline)
- `services/support_resistance.py` — pivot-point S/R detection and strike validation
- `services/expected_move.py` — implied vs. forecast expected move edge classification
- `services/regime_transition.py` — regime transition detection, confidence, direction tracking

---

# 2. Current Readiness State

## Working and live
- Databento daily bars → real SMA/ATR/ADX/RSI/HV20
- Live Polygon options chain normalization
- Real `iv_hv_ratio`
- Options context snapshot (PCR, skew, expected move 1d/1w/30d, chain confidence)
- Options context score adjustment and hard-reject for untradeable chains
- Watchlist-driven scans
- Config-driven spread selection (BULL strategies; see gap below)
- Spread scoring model
- Paper-live validation logging and review tooling
- 280 tests passing

## Known gaps (code-confirmed)
| Gap | Location | Impact |
|---|---|---|
| `iv_rank` not auto-accumulating | `run_nightly_scan.py` imports but never calls `append_iv_proxy_observation` | IV rank stays placeholder until 60 obs/symbol exist |
| Bear spread construction missing | `expiration_aware_spread_selector.py` only handles `BULL_PUT_SPREAD` and `BULL_CALL_SPREAD` | Bear-regime signals produce zero trade candidates |
| `iv_rv_spread` always None | `feature_normalizer.py` passes `iv_rv_spread=None` to `classify_iv_state` | Third IV-rich signal inactive; IV_RICH requires both rank ≥ 60 AND iv_hv ≥ 1.25 |
| Continuous scoring not used | `decision_engine.py` calls `score_candidate` with booleans only (no `adx`, `iv_ratio`, `breadth_distance`) | All qualified candidates score 100.0 before context adjustment |
| `vix_defensive` hardwired False | `feature_normalizer.py` | RISK_OFF regime unreachable |

## Strict-live note
Strict-live (`OPTIONS_ALGO_STRICT_LIVE_MODE=1`) is intentionally blocked whenever placeholder IV rank inputs remain. This is a safety gate.

---

# 3. Repository Structure

## Core scripts (`scripts/`)
| Script | Purpose |
|---|---|
| `run_nightly_scan.py` | Core scan entry point; returns path to scan artifact |
| `run_trade_ideas.py` | Scan + print trade idea summary |
| `run_paper_live_daily.py` | Scan + append validation logs |
| `run_strict_live_scan.py` | Run with strict-live mode enforced |
| `run_sample_scan.py` | Quick scan against mock series (no API keys) |
| `inspect_scan_debug.py` | Per-symbol feature debug and decision trace inspector |
| `inspect_scan_result.py` | Raw scan artifact inspector |
| `review_paper_live_logs.py` | Multi-run pass rate, rejection reasons, regime/IV distribution |
| `paper_live_symbol_leaderboard.py` | Per-symbol pass frequency, ADX, IV/HV profile |
| `build_watchlist.py` | Build underlying interest watchlist |
| `build_options_watchlist.py` | Add options viability data to watchlist |
| `filter_options_watchlist.py` | Filter to viable options names |
| `build_options_context_snapshot.py` | Compute and persist options context for a watchlist |
| `show_databento_runtime_info.py` | Inspect Databento API connectivity and bar availability |
| `debug_polygon_chain_payload.py` | Inspect raw Polygon chain response for a symbol |
| `test_live_historical_rows.py` | Databento live connectivity smoke test |
| `test_live_options_chain.py` | Polygon chain connectivity smoke test |

## Key config
| File | Contents |
|---|---|
| `config/strategy_v1.yaml` | DTE bands, delta bands, breadth thresholds, IV rank min obs, extension ATR multiple |
| `config/universe_v1.yaml` | 58-symbol universe across all 11 GICS sectors |
| `config/risk_v1.yaml` | Min price/volume/OI, max spread, quote ages, risk per trade, max positions |

## Core services (`src/options_algo_v2/services/`)
| File | Purpose |
|---|---|
| `feature_normalizer.py` | Delegates to classifiers, builds `PipelineEvaluationPayload` |
| `decision_engine.py` | Strategy selector → hard filters → score → `CandidateDecision` |
| `candidate_ranker.py` | `score_candidate` — 100-pt scoring |
| `options_context_decision_adjuster.py` | Chain confidence/PCR/skew score delta and hard-reject |
| `trade_candidate_ranking.py` | Spread scoring + context ranking adjustment |
| `spread_scoring.py` | `score_bull_put_spread` / `score_bull_call_spread` |
| `expiration_aware_spread_selector.py` | Config-driven spread selection (BULL strategies currently) |
| `iv_rank_history.py` | IV rank computation and history persistence |
| `iv_feature_estimator.py` | Near-ATM IV proxy, HV20, IV/HV ratio |
| `options_context_service.py` | Chain quality, expected move, positioning, skew, confidence |
| `mock_historical_rows.py` | Calibrated mock price series for testing |

## Key output directories
- `data/scan_results/` — `scan_<run_id>.json` artifacts
- `data/watchlists/` — watchlist JSON files
- `data/validation/` — paper-live JSONL/CSV logs
- `data/state/` — `iv_proxy_history.jsonl`

---

# 4. Environment Setup

## 4.1 Python environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 4.2 Environment variables
```bash
set -a
source .env
set +a
```

Required for live mode:
```
OPTIONS_ALGO_RUNTIME_MODE=live
DATABENTO_API_KEY=...
POLYGON_API_KEY=...
```

Optional runtime flags:
```
OPTIONS_ALGO_STRICT_LIVE_MODE=1          # enable strict-live blocking
OPTIONS_ALGO_BREADTH_OVERRIDE_PCT_ABOVE_20DMA=55.0  # override breadth value
MARKET_HISTORY_DB_PATH=data/cache/market_history_watchlist60.db  # SQLite IV history
```

---

# 5. Runtime Concepts

## Runtime modes
- `mock` (default) — uses mock bar series and fixed IV inputs; no API calls required
- `live` — uses Databento + Polygon; requires API keys

## Strict-live mode
Blocks runs if any of these are true:
- `used_placeholder_iv_rank_inputs = True`
- `used_placeholder_iv_hv_ratio_inputs = True`
- `used_placeholder_liquidity_inputs = True`

Use this only to verify readiness, not for normal paper-live operation.

## Degraded live mode
A run may still complete in paper-live while `degraded_live_mode = True`. Causes:
- placeholder IV rank (most common currently)
- breadth override
- mock historical fallback

This is acceptable for paper-live validation but not for true strict-live execution.

## Options context modes
In mock mode: missing context applies −4 score penalty (advisory only, no hard reject).
In live mode: missing context applies −8 penalty (no hard reject unless confidence < 0.50 AND chain regime is thin/illiquid).

---

# 6. Daily Operating Workflows

## Workflow A — Run trade ideas directly
Use when you want immediate scan output on a watchlist.

```bash
set -a; source .env; set +a

PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<your_watchlist>.json
```

Output: run summary, rejection reason counts, strategy type counts, top trade candidates by spread score, trade ideas if candidates pass.

---

## Workflow B — Paper-live daily run (standard daily path)
```bash
set -a; source .env; set +a

PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<your_watchlist>.json
```

Appends to:
- `data/validation/paper_live_runs.jsonl`
- `data/validation/paper_live_symbol_decisions.jsonl`
- `data/validation/paper_live_runs.csv`

---

## Workflow C — Strict-live check
```bash
set -a; source .env; set +a

OPTIONS_ALGO_STRICT_LIVE_MODE=1 \
PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<your_watchlist>.json
```

Expected to fail while placeholder IV rank inputs remain. Treat failure as a safety gate.

---

## Workflow D — Recommended daily loop
```bash
set -a; source .env; set +a

PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json

PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5

PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5
```

---

# 7. Watchlist Workflow

## Standard flow
```bash
# Step 1: build underlying interest watchlist
PYTHONPATH=src python scripts/build_watchlist.py

# Step 2: add options viability data
PYTHONPATH=src python scripts/build_options_watchlist.py

# Step 3: filter to viable options names
PYTHONPATH=src python scripts/filter_options_watchlist.py

# Step 4: run scan on result
PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

---

# 8. Inspecting Scan Results

## Find latest scan artifact
```bash
python - <<'PY'
from pathlib import Path
files = sorted(Path("data/scan_results").glob("scan_*.json"))
print(files[-1] if files else "no scan files found")
PY
```

## Inspect per-symbol debug
```bash
PYTHONPATH=src python scripts/inspect_scan_debug.py data/scan_results/<scan_file>.json
```

Shows per symbol:
- `close`, `dma20`, `dma50`, `atr20`, `adx14`, `rsi14`, `iv_rank`, `iv_hv_ratio`
- `market_breadth_pct_above_20dma`
- directional checks (close > dma20, adx ≥ 18, RSI in range, not extended)
- `directional_state`, `market_regime`, `iv_state`
- `strategy_type`, `signal_state`
- `final_score`, `min_score_required`
- rejection reasons from each filter layer
- options context debug (confidence, regime, PCR, expected move)

Use this first when a run produces no candidates or unexpected behavior.

## Inspect raw JSON artifact
```bash
python - <<'PY'
import json
from pathlib import Path
files = sorted(Path("data/scan_results").glob("scan_*.json"))
payload = json.loads(files[-1].read_text())
print("summary:", payload["summary"])
print("trade_ideas:", len(payload.get("trade_ideas", [])))
rm = payload["runtime_metadata"]
print("iv_rank_ready_symbols:", rm.get("iv_rank_ready_symbols"))
print("iv_rank_insufficient_history_symbols:", rm.get("iv_rank_insufficient_history_symbols"))
print("options_context_matched_count:", rm.get("options_context_matched_count"))
PY
```

---

# 9. Reviewing Paper-Live Logs

## Recent runs summary
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5
```

## Specific symbol
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5 --symbol XLE
```

## Since a date
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py --since-date 2026-03-01
```

Helps answer: pass rate, repeated passing symbols, rejection reason distribution, directional/IV state distribution, strategy-family mix.

---

# 10. Symbol Leaderboard

## Default (all history)
```bash
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py
```

## Last N runs
```bash
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 10
```

## Sort by ADX or IV/HV
```bash
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 10 --sort-by avg_adx14
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 10 --sort-by avg_iv_hv_ratio
```

Helps answer: which symbols repeatedly pass, which are persistently neutral, ADX and IV/HV strength profiles.

---

# 11. IV Rank History

## Current state
`iv_rank` uses a 60-observation rolling percentile rank. Until 60 observations exist per symbol, the fallback is 50.0 (neutral). IV state therefore defaults to IV_NORMAL or IV_CHEAP for most symbols until history accumulates.

**Important**: The live scan currently does not auto-write observations. `append_iv_proxy_observation` exists in `services/iv_rank_history.py` but is not called from `run_nightly_scan.py`. IV proxy history must be written by a separate process until this is wired in.

## Storage location
```
data/state/iv_proxy_history.jsonl
```

Each line: `{"as_of_date": "2026-03-22", "symbol": "AAPL", "implied_vol_proxy": 0.28, "source": "polygon_near_atm"}`

## Inspect counts
```bash
python - <<'PY'
import json
from collections import Counter
from pathlib import Path
path = Path("data/state/iv_proxy_history.jsonl")
if not path.exists():
    print("no history file")
else:
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    counts = Counter(r["symbol"] for r in rows)
    for sym, count in sorted(counts.items()):
        print(f"{sym}: {count} observations (need 60)")
PY
```

## Readiness in scan metadata
```bash
python - <<'PY'
import json
from pathlib import Path
files = sorted(Path("data/scan_results").glob("scan_*.json"))
rm = json.loads(files[-1].read_text())["runtime_metadata"]
print("iv_rank_ready_symbols:", rm.get("iv_rank_ready_symbols"))
print("iv_rank_insufficient_history_symbols:", rm.get("iv_rank_insufficient_history_symbols"))
print("observation_counts:", rm.get("iv_rank_observation_count_by_symbol"))
PY
```

---

# 12. Configuration Reference

## strategy_v1.yaml — key parameters
| Parameter | Value | Description |
|---|---|---|
| `breadth_bullish_threshold` | 52.0 | Breadth % above which regime is bullish |
| `breadth_bearish_threshold` | 48.0 | Breadth % below which regime is bearish |
| `iv_rank_min_observations` | 60 | Min observations before iv_rank is real |
| `adx_trending_min` | 18.0 | Min ADX for directional qualification |
| `extension_atr_multiple` | 2.0 | ATR multiples from DMA20 for extension |
| `credit_dte_min/target/max` | 25/35/45 | DTE window for credit spreads |
| `debit_dte_min/target/max` | 14/28/45 | DTE window for debit spreads |
| `credit_short_delta_min/target/max` | 0.15/0.22/0.30 | Short-leg delta for credit spreads |
| `debit_long_delta_min/target/max` | 0.45/0.55/0.65 | Long-leg delta for debit spreads |
| `iv_rich_rank_min` | 60.0 | IV rank threshold for IV_RICH signal |
| `iv_cheap_rank_max` | 30.0 | IV rank threshold for IV_CHEAP signal |
| `iv_hv_rich_min` | 1.25 | IV/HV ratio threshold for IV_RICH signal |
| `iv_hv_cheap_max` | 1.05 | IV/HV ratio threshold for IV_CHEAP signal |

## risk_v1.yaml — key parameters
| Parameter | Value |
|---|---|
| `min_underlying_price` | 20.0 |
| `min_avg_daily_volume` | 1,000,000 |
| `min_option_open_interest` | 250 |
| `min_option_volume` | 50 |
| `max_bid_ask_spread_pct` | 0.08 (8%) |
| `max_option_quote_age_seconds` | 60 |
| `max_underlying_quote_age_seconds` | 10 |
| `min_candidate_score` | 70.0 |
| `max_risk_per_trade_pct` | 1.0% |
| `max_open_positions` | 5 |
| `max_positions_per_sector` | 2 |

---

# 13. Interpreting Common Outcomes

## No candidates passed
Check `inspect_scan_debug.py`. Common causes:
- all symbols NEUTRAL — ADX below 18 or RSI outside [45, 85]
- breadth near 50% → RANGE_UNCLEAR → BULL_CALL_SPREAD rejected (only credit spreads allowed in RANGE_UNCLEAR)
- extended symbols (close > DMA20 + 2×ATR20)
- liquidity failures on option quotes
- options context hard-reject (low confidence + illiquid chain in live mode)

## One symbol repeatedly passes
Not a bug. Interpret as:
- current rules produce sparse, high-conviction signals
- that symbol has the clearest alignment in the current regime
- avoid lowering thresholds based on a handful of runs

## Trade candidates exist but no trade ideas appear
Check spread selection:
- bear-strategy symbols currently return no trade candidates (known gap)
- BULL_PUT / BULL_CALL spreads need eligible expirations in the 25–45 DTE window
- options context hard-reject may have removed the candidate post-scoring

## Strict-live fails
Expected when:
- placeholder IV rank is in use
- `used_placeholder_iv_inputs = True` in runtime metadata
This is a safety feature.

---

# 14. Troubleshooting

## No scan files in `data/scan_results/`
- Confirm `.env` loaded and run completed without error
- Check correct watchlist path
- Confirm API keys set for live mode

## Live provider errors
```bash
set -a; source .env; set +a  # always load env first
```
Common causes: missing `DATABENTO_API_KEY`, missing `POLYGON_API_KEY`, live market breadth provider not configured.

## Options context missing for all symbols
The options context is loaded from `data/validation/latest_options_context.json` if it exists. In most paper-live runs this file will not be present (it is produced by the options context pipeline, not by `run_paper_live_daily.py` directly). Missing context applies a score penalty but does not hard-reject in mock mode.

## `iv_rank` stays placeholder
Expected until 60 daily observations exist per symbol. Monitor with:
```bash
tail -n 20 data/state/iv_proxy_history.jsonl
```
or use the count script in section 11.

## Bear-regime candidates produce no trade ideas
Known gap. `expiration_aware_spread_selector.py` returns `[]` for BEAR_CALL_SPREAD and BEAR_PUT_SPREAD. The signal will qualify and score correctly; it simply has no spread candidates built. Fix is pending.

## `clean_test: command not found`
Use the raw commands:
```bash
pytest
ruff check .
mypy src
```

---

# 15. Validation / Quality Commands

```bash
pytest              # 280 tests, all should pass
ruff check .        # lint (expect clean)
mypy src            # type check
```

Run these before pushing any code changes.

---

# 16. Git Workflow

```bash
git status --short
git branch --show-current
git add .
git commit -m "type(scope): description"
git push origin <branch>
```

Commit discipline: separate commits for feature pipeline changes, config changes, logging/tooling changes, and docs updates.

---

# 17. Operational Boundaries

## Safe now
- daily paper-live runs and artifact inspection
- review logs and leaderboard
- watchlist experimentation
- strategy observation
- IV history accumulation (manual or via a separate write process)

## Not yet safe
- unattended strict-live execution
- bear-regime signal-to-trade pipeline (spread construction missing)
- small-capital live deployment

---

# 18. Recommended Near-Term Priorities

1. **Wire `append_iv_proxy_observation`** into `run_nightly_scan.py` so IV proxy history accumulates automatically every live run
2. **Add bear spread construction** to `expiration_aware_spread_selector.py`
3. **Populate `iv_rv_spread`** from IV proxy minus HV20 so the third IV signal activates
4. **Pass continuous ADX/IV/breadth to `score_candidate`** in `decision_engine.py` for finer candidate differentiation
5. **Wire `expected_move.py`** into trade candidate filtering
6. **Wire `support_resistance.py`** into strike selection validation
7. **Wire `regime_transition.py`** into entry scoring or timing
8. **Continue daily paper-live validation** and accumulate IV history
9. **Complete production hardening** (breadth freshness, quote-quality thresholds, risk caps, monitoring)
10. **Enable strict-live** only after placeholder IV rank is eliminated

---

# 19. Quick Command Reference

```bash
# Load environment
set -a; source .env; set +a

# Run trade ideas
PYTHONPATH=src python scripts/run_trade_ideas.py --watchlist data/watchlists/<file>.json

# Run paper-live daily
PYTHONPATH=src python scripts/run_paper_live_daily.py --watchlist data/watchlists/<file>.json

# Inspect latest scan
PYTHONPATH=src python scripts/inspect_scan_debug.py data/scan_results/<scan>.json

# Review paper-live logs
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5

# Symbol leaderboard
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5

# IV history tail
tail -n 20 data/state/iv_proxy_history.jsonl

# Validate code
pytest && ruff check . && mypy src

# Strict-live check
OPTIONS_ALGO_STRICT_LIVE_MODE=1 PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<file>.json
```
