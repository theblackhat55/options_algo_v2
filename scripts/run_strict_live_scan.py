from __future__ import annotations

import os

from run_nightly_scan import run_nightly_scan


def main() -> str:
    os.environ["OPTIONS_ALGO_RUNTIME_MODE"] = "live"
    os.environ["OPTIONS_ALGO_STRICT_LIVE_MODE"] = "true"
    os.environ["OPTIONS_ALGO_ALLOW_MOCK_HISTORICAL_FALLBACK"] = "false"
    os.environ["OPTIONS_ALGO_ALLOW_BREADTH_OVERRIDE"] = "false"
    os.environ["OPTIONS_ALGO_ALLOW_SHORT_DTE_FALLBACK"] = "false"
    os.environ["OPTIONS_ALGO_ALLOW_RELAXED_LIQUIDITY_THRESHOLDS"] = "false"

    return run_nightly_scan()


if __name__ == "__main__":
    main()
