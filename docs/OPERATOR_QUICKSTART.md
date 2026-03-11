Use this to create `OPERATOR_QUICKSTART.md`:

```bash
cat > OPERATOR_QUICKSTART.md <<'MD'
# OPERATOR QUICKSTART

## Purpose
This is the shortest practical guide for running the platform day to day.

Use this if you want to:
- load the environment
- run a paper-live scan
- inspect the result
- review recent logs
- check whether IV rank is still placeholder-driven

For full detail, see `RUNBOOK.md`.

---

# 1. Load environment

```bash
set -a
source .env
set +a
```

Activate the virtualenv first if needed:

```bash
source .venv/bin/activate
```

---

# 2. Recommended daily workflow

## Run the daily paper-live flow
```bash
PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

Example:
```bash
PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/options_watchlist_filtered_20260311T133308Z.json
```

### What this does
- runs the live scan
- writes a scan artifact to `data/scan_results/`
- appends run logs to:
  - `data/validation/paper_live_runs.jsonl`
  - `data/validation/paper_live_symbol_decisions.jsonl`
  - `data/validation/paper_live_runs.csv`

---

# 3. Inspect the latest scan

## Find the latest scan file
```bash
python - <<'PY'
from pathlib import Path
files = sorted(Path("data/scan_results").glob("scan_*.json"))
print(files[-1] if files else "no scan files found")
PY
```

## Inspect it
```bash
PYTHONPATH=src python scripts/inspect_scan_debug.py data/scan_results/<scan_file>.json
```

This shows:
- raw features
- directional checks
- decision state
- rejection reasons
- provider metadata

Use this first whenever a run looks odd.

---

# 4. Review recent paper-live logs

## Recent runs
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5
```

## Specific symbol
```bash
PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5 --symbol XLE
```

## Leaderboard
```bash
PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5
```

Useful for spotting:
- repeated winners
- repeated neutral names
- repeated bearish names in up regime
- pass-rate stability

---

# 5. Check IV rank readiness

## Inspect readiness from latest scan metadata
```bash
python - <<'PY'
import json
from pathlib import Path

latest = sorted(Path("data/scan_results").glob("scan_*.json"))[-1]
payload = json.loads(latest.read_text())
rm = payload.get("runtime_metadata", {})

for key in [
    "iv_rank_ready_symbols",
    "iv_rank_insufficient_history_symbols",
    "iv_rank_history_path",
    "iv_rank_trailing_observations",
]:
    print(f"{key}: {rm.get(key)}")
PY
```

## Inspect IV proxy history
```bash
tail -n 20 data/state/iv_proxy_history.jsonl
```

### Expected current behavior
If IV rank is still building history, you will see:
- `iv_rank_ready_symbols: []`
- `iv_rank_insufficient_history_symbols: [...]`

That is normal until enough daily observations accumulate.

---

# 6. Run trade ideas directly

If you want trade idea output immediately:

```bash
PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

This prints:
- run summary
- rejection reason counts
- strategy mix
- trade idea details if any candidates pass

---

# 7. Strict-live check

Only use this when you want to confirm whether the system would pass strict-live policy.

```bash
OPTIONS_ALGO_STRICT_LIVE_MODE=1 \
PYTHONPATH=src python scripts/run_trade_ideas.py \
  --watchlist data/watchlists/<filtered_watchlist>.json
```

### Important
If placeholder IV inputs are still present, strict-live should fail.  
That is expected and desirable.

---

# 8. Quick troubleshooting

## `clean_test: command not found`
Use:
```bash
pytest
ruff check .
mypy src
```

## No scan artifact found
Check:
- `.env` loaded
- correct watchlist path
- API keys set
- script finished successfully

## Strict-live fails
Usually because:
- `iv_rank` is still placeholder
- degraded mode was triggered
- provider data was unavailable

---

# 9. Daily operator checklist

Run these in order:

```bash
set -a
source .env
set +a

PYTHONPATH=src python scripts/run_paper_live_daily.py \
  --watchlist data/watchlists/<filtered_watchlist>.json

PYTHONPATH=src python scripts/review_paper_live_logs.py --last-runs 5

PYTHONPATH=src python scripts/paper_live_symbol_leaderboard.py --last-runs 5
```

Then check:
- passed count
- repeated passing symbols
- rejection reason distribution
- whether `iv_rank_ready_symbols` has started filling in

---

# 10. Validation commands

Before pushing code changes:

```bash
pytest
ruff check .
mypy src
```

---

# 11. Current operating guidance

## Safe now
- daily paper-live runs
- scan inspection
- log review
- IV history accumulation
- watchlist experimentation

## Not yet assumed safe
- unattended strict-live production operation
- small-capital live deployment before IV rank is fully real and hardening is complete

For complete operating detail, see `RUNBOOK.md`.
MD
```

Then commit it:

```bash
git add OPERATOR_QUICKSTART.md
git commit -m "docs: add operator quickstart guide"
git push origin main
```
