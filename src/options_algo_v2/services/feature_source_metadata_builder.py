from __future__ import annotations

from options_algo_v2.domain.feature_source_metadata import FeatureSourceMetadata
from options_algo_v2.services.databento_runtime_info import build_databento_runtime_info
from options_algo_v2.services.historical_row_provider_factory import (
    get_historical_row_provider_name,
)
from options_algo_v2.services.market_breadth_provider_factory import (
    get_market_breadth_provider_name,
)


def build_feature_source_metadata(*, symbol: str) -> FeatureSourceMetadata:
    databento_runtime = build_databento_runtime_info()

    return FeatureSourceMetadata(
        symbol=symbol,
        historical_row_provider=get_historical_row_provider_name(),
        market_breadth_provider=get_market_breadth_provider_name(),
        dataset=databento_runtime["dataset"],
        schema=databento_runtime["schema"],
    )
