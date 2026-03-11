Below is a **detailed `RUNBOOK.md`** you can add to the repo.

Use this command to create it:

```bash
cat > RUNBOOK.md <<'MD'
# RUNBOOK

## Purpose
This runbook explains how to operate the `options_algo_v2` platform end-to-end, from environment setup through daily paper-live use, diagnostics, validation review, and strict-live readiness checks.

It is written for an operator or developer who needs to:
- run scans
- build and filter watchlists
- inspect failures
- review paper-live logs
- understand current readiness limits

---

# 1. Platform Overview

## What this platform does
The platform scans underlyings, computes market/technical/volatility features, selects options spread candidates, and produces trade ideas.

At a high level the flow is:

1. **Universe / watchlist input**
2. **Historical feature computation**
   - close
   - 20-day / 50-day moving averages
   - ATR20
   - ADX14
3. **Market breadth + regime context**
4. **Options chain retrieval**
5. **Volatility context**
   - `iv_hv_ratio` from live option IV proxy + historical vol
   - `iv_rank` from persisted IV proxy history when enough observations exist
6. **Decision engine**
7. **Spread selection**
8. **Trade candidate / trade idea generation**
9. **Artifact generation**
10. **Paper-live validation logging**

---

# 2. Current Readiness State

## Real / live inputs already in use
- Databento historical daily bars
- live market breadth provider
- Polygon live options chain
- real SMA / ATR / ADX
- real `iv_hv_ratio`
- persisted IV proxy history
- watchlist-driven scans
- paper-live validation logs and review tooling

## Still transitional
- `iv_rank` may remain placeholder until enough daily IV history accumulates

## Strict-live note
Strict-live should remain blocked whenever placeholder IV inputs are still present.

---

# 3. Repository Structure You Will Use Most

## Core scripts
- `scripts/run_nightly_scan.py`
- `scripts/run_trade_ideas.py`
- `scripts/run_paper_live_daily.py`
- `scripts/inspect_scan_debug.py`
- `scripts/review_paper_live_logs.py`
- `scripts/paper_live_symbol_leaderboard.py`
- `scripts/build_watchlist.py`
- `scripts/filter_options_watchlist.py`
- `scripts/build_options_watchlist.py`
- `scripts/run_strict_live_scan.py`

## Key docs
- `docs/live_status_summary.md`
- `docs/go_live_phases.md`
- `docs/go_live_plan_v2_1.md` (if added)
- `docs/watchlist_design.md`
- `docs/options_watchlist_policy.md`

## Key output directories
- `data/scan_results/`
- `data/watchlists/`
- `data/validation/`
- `data/state/`

---

# 4. Environment Setup

## 4.1 Python environment
Create and activate the virtual environment if needed:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies according to your project’s existing setup.

If your repo uses editable install:
```bash
pip install -e .
```

If it uses requirements:
```bash
pip install -r requirements.txt
```

If it uses Poetry/uv, follow the repo-standard install method.

---

## 4.2 Environment variables
Load the environment before live or paper-live runs:

```bash
set -a
source .env
set +a
```

At minimum, live mode typically requires:
- `OPTIONS_ALGO_RUNTIME_MODE=live`
- `DATABENTO_API_KEY=...`
- `POLYGON_API_KEY=...`

Additional runtime flags may exist, including:
- strict-live mode
- breadth override settings
- degraded-data policy toggles

---

# 5. Important Runtime Concepts

## Runtime mode
The platform supports at least:
- `mock`
- `live`

Live mode uses real Databento / Polygon providers.

## Strict-live mode
Strict-live is designed to block runs that rely on degraded or placeholder inputs.

Examples of conditions that should block strict-live:
- placeholder IV inputs
- mock historical fallback
- disallowed breadth override
- future stale-data/quote-quality policies

## Degraded live mode
A run may still complete in paper-live while marked degraded.

Typical causes:
- placeholder IV rank
- breadth override
- mock historical fallback

This is acceptable for validation but not acceptable for true strict-live execution.

---

# 6. Daily Operating Workflows

There are three main ways to use the platform.

## Workflow A — Run a direct trade-idea scan on a watchlist
Use this when you already have a watchlist and want immediate scan/trade idea output.

```bash
set -a
source .env
set +a

PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<your_watchlist>.json
```

### What it does
- runs the nightly scan
- evaluates decisions
- selects spreads
- prints summary and trade ideas
- writes a scan artifact under `data/scan_results/`

### Typical output includes
- run ID
- output artifact path
- total / passed / rejected counts
- rejection reason counts
- strategy type counts
- top trade candidate symbols
- trade idea details

---

## Workflow B — Paper-live daily run (recommended daily path)
Use this as the standard daily operational loop.

```bash
set -a
source .env
set +a

PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<your_watchlist>.json
```

### What it does
- runs a live scan on the given watchlist
- writes the scan artifact
- appends run-level logs to JSONL and CSV
- appends symbol-level logs to JSONL

### Validation outputs
- `data/validation/paper_live_runs.jsonl`
- `data/validation/paper_live_symbol_decisions.jsonl`
- `data/validation/paper_live_runs.csv`

This is the main daily paper-live workflow.

---

## Workflow C — Strict-live check
Use this only when you want to verify whether the system is ready to run without placeholder/degraded inputs.

Example:
```bash
set -a
source .env
set +a

OPTIONS_ALGO_STRICT_LIVE_MODE=1 \
PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<your_watchlist>.json
```

### Expected behavior
- if placeholder IV inputs remain, the run should fail fast
- if all strict-live requirements are satisfied, the run should complete

Do **not** treat strict-live success as automatic approval for real-money trading unless the rest of the production hardening checklist is also complete.

---

# 7. Watchlist Workflow

There are two practical operating modes:
- use an existing filtered watchlist
- build / filter watchlists as part of the daily process

## 7.1 Build a broader watchlist
If your repo supports it:

```bash
PYTHONPATH=src python scripts/build_watchlist.py
```

This should generate a broader underlying-interest watchlist.

## 7.2 Build options-oriented watchlist
If applicable:

```bash
PYTHONPATH=src python scripts/build_options_watchlist.py
```

## 7.3 Filter watchlist to viable options names
```bash
PYTHONPATH=src python scripts/filter_options_watchlist.py
```

## 7.4 Run trade ideas on the filtered watchlist
```bash
PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

## Recommended future daily flow
```bash
set -a
source .env
set +a

PYTHONPATH=src python scripts/build_watchlist.py
PYTHONPATH=src python scripts/filter_options_watchlist.py
PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

---

# 8. How to Inspect Scan Results

## 8.1 Find the latest scan artifact
```bash
python - <<'PY'
from pathlib import Path
files = sorted(Path("data/scan_results").glob("scan_*.json"))
print(files[-1] if files else "no scan files found")
PY
```

## 8.2 Inspect the latest scan
```bash
PYTHONPATH=src python scripts/inspect_scan_debug.py data/scan_results/<scan_file>.json
```

### What the inspector shows
For each symbol it may display:
- provider source metadata
- `close`
- `dma20`
- `dma50`
- `atr20`
- `adx14`
- `iv_rank`
- `iv_hv_ratio`
- `market_breadth_pct_above_20dma`
- directional checks
- `directional_state`
- `market_regime`
- `iv_state`
- `signal_state`
- `strategy_type`
- `final_score`
- rejection reasons
- filter results

This is the first tool to use when a run produces no candidates or strange behavior.

---

# 9. How to Review Paper-Live Logs

## 9.1 Review recent runs
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5
```

## 9.2 Review a specific symbol
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py \
  --last-runs 5 \
  --symbol XLE
```

## 9.3 Review since a date
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py \
  --since-date 2026-03-11
```

### What this script helps answer
- how many runs were logged
- pass rate across runs
- repeated passed symbols
- common rejection reasons
- directional-state distribution
- IV state distribution
- strategy-family mix

---

# 10. How to Use the Symbol Leaderboard

## Default leaderboard
```bash
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py
```

## Recent runs only
```bash
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5
```

## Sort by average ADX
```bash
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py \
  --last-runs 5 \
  --sort-by avg_adx14
```

## Sort by IV/HV ratio
```bash
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py \
  --last-runs 5 \
  --sort-by avg_iv_hv_ratio
```

### What the leaderboard helps answer
- which symbols repeatedly pass
- which symbols are repeatedly neutral
- which symbols are repeatedly bearish in an up regime
- which symbols show strong ADX but still fail due to MA alignment
- whether one symbol is dominating the opportunity set

---

# 11. IV Rank History Operations

## Where IV proxy history is stored
```text
data/state/iv_proxy_history.jsonl
```

Each row represents a daily implied-vol proxy observation for a symbol.

## Inspect recent IV proxy history
```bash
tail -n 20 data/state/iv_proxy_history.jsonl
```

## Readiness metadata
Recent runs should expose:
- `iv_rank_ready_symbols`
- `iv_rank_insufficient_history_symbols`
- `iv_rank_history_path`
- `iv_rank_trailing_observations`

## Why this matters
Even though `iv_hv_ratio` is already real, `iv_rank` requires enough daily history before it can stop falling back to placeholders.

### Expected near-term behavior
- `iv_rank_ready_symbols=[]`
- `iv_rank_insufficient_history_symbols=[...]`

### Expected later behavior
As more days accumulate:
- some symbols move into `iv_rank_ready_symbols`
- placeholder IV rank usage shrinks
- strict-live readiness improves

---

# 12. Recommended Daily Operator Loop

## Current recommended daily loop
```bash
set -a
source .env
set +a

PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json

PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5

PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5
```

## What to watch daily
- passed count
- repeated passed symbols
- `directional state is not actionable` frequency
- `strategy not permitted in current regime` frequency
- whether degraded mode is still present
- whether placeholder IV rank symbols begin shrinking

---

# 13. Interpreting Common Outcomes

## Case A — No candidates passed
First inspect:
```bash
PYTHONPATH=src python scripts/inspect_scan_debug.py data/scan_results/<scan>.json
```

Common causes:
- most symbols are `NEUTRAL`
- ADX below threshold
- `close <= dma20`
- `dma20 <= dma50`
- bearish continuation in an up regime
- quote quality / viability failures (once these are fully exposed)

## Case B — One symbol repeatedly passes
This is not necessarily a bug.

Interpret it as:
- the current rules are sparse
- that symbol may be the clearest fit for the strategy
- broader universe or more days may be needed before changing thresholds

## Case C — Strict-live fails
This is expected if:
- placeholder IV rank is still in use
- degraded live mode is triggered
- future hardening checks reject the run

Treat strict-live failure as a **safety feature**, not a malfunction.

---

# 14. Troubleshooting

## 14.1 `clean_test: command not found`
Some environments may not have the `clean_test` helper available.

Use raw commands instead:
```bash
pytest
ruff check .
mypy src
```

## 14.2 No scan files found
Ensure the run completed successfully and wrote output to:
```text
data/scan_results/
```

## 14.3 Live provider errors
Common causes:
- `.env` not loaded
- missing `DATABENTO_API_KEY`
- missing `POLYGON_API_KEY`
- live market breadth provider not configured

Always load env before live operations:
```bash
set -a
source .env
set +a
```

## 14.4 Strict-live blocks because of placeholder IV inputs
This is expected until `iv_rank` is fully real.

Check:
- `iv_rank_ready_symbols`
- `iv_rank_insufficient_history_symbols`
- `data/state/iv_proxy_history.jsonl`

## 14.5 Trade idea output looks empty or odd
Inspect the latest scan artifact and review:
- trade candidate fields
- strategy family
- option leg symbols
- spread width / debit / credit
- final score and rationale

Use:
```bash
PYTHONPATH=src python scripts/inspect_scan_debug.py data/scan_results/<scan>.json
```

---

# 15. Validation / Quality Commands

## Run tests
```bash
pytest
```

## Lint
```bash
ruff check .
```

## Type check
```bash
mypy src
```

## Recommended before pushing changes
```bash
pytest
ruff check .
mypy src
```

---

# 16. Git / Release Workflow

## Inspect repo state
```bash
git status --short
git branch --show-current
```

## Commit changes
```bash
git add .
git commit -m "your commit message"
git push origin main
```

## Recommended commit practice
Use separate commits for:
- feature pipeline changes
- strict-live policy changes
- logging/review tooling
- docs/runbook updates

---

# 17. Operational Boundaries

## Safe to do now
- run paper-live daily
- inspect scan artifacts
- review logs and leaderboard
- accumulate IV proxy history
- refine watchlist workflow
- continue validation

## Not yet safe to assume
- unattended strict-live production readiness
- small-capital live deployment
- threshold changes based on only a handful of runs

---

# 18. Recommended Near-Term Priorities

1. Continue daily paper-live runs
2. Let IV rank history accumulate
3. Watch for `iv_rank_ready_symbols` to become non-empty
4. Continue multi-run leaderboard/review analysis
5. Complete remaining quote-quality and production-hardening tasks
6. Only then re-evaluate strict-live readiness

---

# 19. Quick Command Reference

## Run trade ideas
```bash
PYTHONPATH=src python scripts/run_trade_ideas.py --watchlist data/watchlists/<file>.json
```

## Run paper-live daily
```bash
PYTHONPATH=src python scripts/run_paper_live_daily.py --watchlist data/watchlists/<file>.json
```

## Inspect latest scan
```bash
PYTHONPATH=src python scripts/inspect_scan_debug.py data/scan_results/<scan>.json
```

## Review paper-live logs
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5
```

## Review symbol leaderboard
```bash
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5
```

## Inspect IV history
```bash
tail -n 20 data/state/iv_proxy_history.jsonl
```

## Validate code
```bash
pytest
ruff check .
mypy src
```

---

# 20. Final Operator Guidance

This platform is now best treated as a **paper-live validated signal platform with growing strict-live readiness**, not yet as a fully production-ready auto-trading system.

Use it to:
- observe real signal behavior
- measure pass frequency
- identify repeated winners and repeated failure modes
- accumulate enough IV history to complete real `iv_rank`
- harden remaining production controls before any true live deployment
MD
```

