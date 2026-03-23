#!/usr/bin/env bash
set -euo pipefail

TOP_N="all"
END_DATE=""
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    all|batch1|batch2|batch3|batch4)
      TOP_N="$1"
      shift
      ;;
    --end-date)
      END_DATE="${2:-}"
      if [[ -z "$END_DATE" ]]; then
        echo "Error: --end-date requires YYYY-MM-DD"
        exit 1
      fi
      shift 2
      ;;
    *)
      if [[ "$1" =~ ^[0-9]+$ ]]; then
        TOP_N="$1"
        shift
      else
        echo "Unknown argument: $1"
        echo "Usage: scripts/run_dynamic_paper_live_daily.sh [all|batch1|batch2|batch3|batch4|INTEGER] [--end-date YYYY-MM-DD]"
        exit 1
      fi
      ;;
  esac
done

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
python scripts/build_watchlist.py ${END_DATE:+--end-date "$END_DATE"}

LATEST_BASE_WATCHLIST="$(ls -1t data/watchlists/watchlist_*.json | head -n 1)"
echo "latest_base_watchlist=${LATEST_BASE_WATCHLIST}"

echo "==> Step 2: build options watchlist"
python scripts/build_options_watchlist.py "${LATEST_BASE_WATCHLIST}"

LATEST_OPTIONS_WATCHLIST="$(ls -1t data/watchlists/options_watchlist_*.json | head -n 1)"
echo "latest_options_watchlist=${LATEST_OPTIONS_WATCHLIST}"

echo "==> Step 3: filter options watchlist"
case "${TOP_N}" in
  all) FILTER_TOP_N="" ;;
  batch1) FILTER_TOP_N="15" ;;
  batch2) FILTER_TOP_N="30" ;;
  batch3) FILTER_TOP_N="45" ;;
  batch4) FILTER_TOP_N="60" ;;
  *)
    if [[ "${TOP_N}" =~ ^[0-9]+$ ]]; then
      FILTER_TOP_N="${TOP_N}"
    else
      echo "Invalid top_n/mode: ${TOP_N}"
      echo "Expected all, batch1, batch2, batch3, batch4, or an integer"
      exit 1
    fi
    ;;
esac

if [[ -z "${FILTER_TOP_N}" ]]; then
  python scripts/filter_options_watchlist.py "${LATEST_OPTIONS_WATCHLIST}"
else
  python scripts/filter_options_watchlist.py "${LATEST_OPTIONS_WATCHLIST}" --top-n "${FILTER_TOP_N}"
fi

LATEST_FILTERED_WATCHLIST="$(ls -1t data/watchlists/options_watchlist_filtered_*.json | head -n 1)"
echo "latest_filtered_watchlist=${LATEST_FILTERED_WATCHLIST}"

echo "==> Step 4: run paper-live daily"
python scripts/run_paper_live_daily.py --watchlist "${LATEST_FILTERED_WATCHLIST}" ${END_DATE:+--end-date "$END_DATE"}

echo "==> Step 5: build OpenClaw report"
python scripts/build_openclaw_options_report.py

echo "==> Done"
echo "top_n=${TOP_N}"
echo "end_date=${END_DATE:-auto}"
echo "base_watchlist=${LATEST_BASE_WATCHLIST}"
echo "options_watchlist=${LATEST_OPTIONS_WATCHLIST}"
echo "filtered_watchlist=${LATEST_FILTERED_WATCHLIST}"
