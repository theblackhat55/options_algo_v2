#!/usr/bin/env bash
set -euo pipefail

TOP_N="${1:-all}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

mkdir -p logs data/watchlists data/scan_results data/validation

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export PYTHONPATH=src

echo "==> Step 1: build base watchlist"
python scripts/build_watchlist.py

LATEST_BASE_WATCHLIST="$(ls -1t data/watchlists/watchlist_*.json | head -n 1)"
echo "latest_base_watchlist=${LATEST_BASE_WATCHLIST}"

echo "==> Step 2: build options watchlist"
python scripts/build_options_watchlist.py "${LATEST_BASE_WATCHLIST}"

LATEST_OPTIONS_WATCHLIST="$(ls -1t data/watchlists/options_watchlist_*.json | head -n 1)"
echo "latest_options_watchlist=${LATEST_OPTIONS_WATCHLIST}"

echo "==> Step 3: filter options watchlist"
if [[ "${TOP_N}" == "all" ]]; then
  python scripts/filter_options_watchlist.py "${LATEST_OPTIONS_WATCHLIST}"
else
  python scripts/filter_options_watchlist.py "${LATEST_OPTIONS_WATCHLIST}" --top-n "${TOP_N}"
fi

LATEST_FILTERED_WATCHLIST="$(ls -1t data/watchlists/options_watchlist_filtered_*.json | head -n 1)"
echo "latest_filtered_watchlist=${LATEST_FILTERED_WATCHLIST}"

echo "==> Step 4: run paper-live daily"
python scripts/run_paper_live_daily.py --watchlist "${LATEST_FILTERED_WATCHLIST}"

echo "==> Done"
echo "top_n=${TOP_N}"
echo "base_watchlist=${LATEST_BASE_WATCHLIST}"
echo "options_watchlist=${LATEST_OPTIONS_WATCHLIST}"
echo "filtered_watchlist=${LATEST_FILTERED_WATCHLIST}"
