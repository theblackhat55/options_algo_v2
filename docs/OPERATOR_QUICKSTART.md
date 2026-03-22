# OPERATOR QUICKSTART

Shortest practical guide for daily platform operation.

For full detail see [`RUNBOOK.md`](RUNBOOK.md).

---

## 1. Load environment

```bash
source .venv/bin/activate
set -a; source .env; set +a
```

Required variables for live mode:

```
OPTIONS_ALGO_RUNTIME_MODE=live
DATABENTO_API_KEY=...
POLYGON_API_KEY=...
```

---

## 2. Daily paper-live run

```bash
PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

Writes:
- `data/scan_results/scan_<run_id>.json`
- `data/validation/paper_live_runs.jsonl`
- `data/validation/paper_live_symbol_decisions.jsonl`
- `data/validation/paper_live_runs.csv`

---

## 3. Review logs

```bash
# Recent runs summary
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5

# Symbol-level leaderboard
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5

# Filter to a specific symbol
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5 --symbol XLE
```

---

## 4. Inspect a scan artifact

```bash
# Find latest scan file
python - <<'PY'
from pathlib import Path
files = sorted(Path("data/scan_results").glob("scan_*.json"))
print(files[-1] if files else "no scan files found")
PY

# Inspect it
PYTHONPATH=src python scripts/inspect_scan_debug.py data/scan_results/<scan_file>.json
```

Shows per-symbol: raw features, directional checks, regime/IV/directional state, strategy type, rejection reasons, options context debug.

Use this first whenever a run produces unexpected output.

---

## 5. Run trade ideas directly

```bash
PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

Prints: run summary, rejection reason counts, strategy mix, top trade candidates, trade ideas.

---

## 6. Check IV rank readiness

```bash
# From latest scan metadata
python - <<'PY'
import json
from pathlib import Path
latest = sorted(Path("data/scan_results").glob("scan_*.json"))[-1]
rm = json.loads(latest.read_text())["runtime_metadata"]
for key in ["iv_rank_ready_symbols", "iv_rank_insufficient_history_symbols",
            "iv_rank_trailing_observations", "iv_rank_history_path"]:
    print(f"{key}: {rm.get(key)}")
PY

# Raw history tail
tail -n 20 data/state/iv_proxy_history.jsonl
```

Until 60 daily observations per symbol exist, `iv_rank` uses a 50.0 placeholder.
`iv_rank_ready_symbols: []` is normal while history is still accumulating.

---

## 7. Strict-live check

Only use when verifying whether the system would pass strict-live policy:

```bash
OPTIONS_ALGO_STRICT_LIVE_MODE=1 \
PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

Expected to fail while `iv_rank` placeholder inputs remain. That is the intended behavior.

---

## 8. Watchlist rebuild

```bash
PYTHONPATH=src python scripts/build_watchlist.py
PYTHONPATH=src python scripts/build_options_watchlist.py
PYTHONPATH=src python scripts/filter_options_watchlist.py
```

---

## 9. Diagnostic scripts

```bash
# Databento connectivity and bar availability
PYTHONPATH=src python scripts/show_databento_runtime_info.py

# Raw Polygon chain payload for a symbol
PYTHONPATH=src python scripts/debug_polygon_chain_payload.py AAPL

# Connectivity smoke tests
PYTHONPATH=src python scripts/test_live_historical_rows.py
PYTHONPATH=src python scripts/test_live_options_chain.py
```

---

## 10. Validation commands

```bash
pytest              # 280 tests, all should pass
ruff check .        # lint
mypy src            # type check
```

---

## 11. Quick troubleshooting

| Symptom | Likely cause |
|---|---|
| No scan artifact | `.env` not loaded, wrong watchlist path, API key missing |
| All symbols NEUTRAL | ADX < 18 or RSI outside [45, 85] in current market |
| No trade ideas despite passing candidates | Bear strategy selected — bear spread construction not yet wired |
| Strict-live fails | Placeholder `iv_rank` still in use — expected behavior |
| `iv_rank_ready_symbols: []` | Normal — 60 observations per symbol needed, still accumulating |

---

## 12. Current operating boundaries

**Safe now:**
- daily paper-live runs
- scan artifact inspection
- log review and leaderboard analysis
- watchlist experimentation
- IV history accumulation

**Not yet safe:**
- unattended strict-live execution
- bear-regime signal-to-trade pipeline (spread construction missing)
- small-capital live deployment
