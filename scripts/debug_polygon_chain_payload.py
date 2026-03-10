from __future__ import annotations

import json
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

from options_algo_v2.services.polygon_settings import PolygonSettings


def main() -> None:
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    settings = PolygonSettings.from_env()

    query = urlencode(
        {
            "limit": 5,
            "apiKey": settings.api_key,
        }
    )
    url = f"{settings.base_url}/v3/snapshot/options/{symbol}?{query}"

    print(f"url={url}")

    with urlopen(url, timeout=settings.timeout_seconds) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))

    print(f"top_level_keys={sorted(payload.keys())}")
    results = payload.get("results", [])
    print(f"results_type={type(results).__name__}")
    print(f"results_count={len(results) if isinstance(results, list) else 'n/a'}")

    if isinstance(results, list) and results:
        first = results[0]
        print("first_result=")
        print(json.dumps(first, indent=2, default=str))
    else:
        print("no results returned")


if __name__ == "__main__":
    main()
