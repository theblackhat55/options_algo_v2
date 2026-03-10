from __future__ import annotations

from datetime import date

from options_algo_v2.domain.raw_features import RawFeatureInput
from options_algo_v2.domain.underlying_data import UnderlyingSnapshot


def build_sample_raw_features_from_snapshot(
    snapshot: UnderlyingSnapshot,
) -> RawFeatureInput:
    bullish_symbols = {"AAPL", "MSFT", "NVDA", "META", "SPY", "QQQ"}
    is_bullish = snapshot.symbol in bullish_symbols

    close = snapshot.close
    dma20 = close - 5.0 if is_bullish else close
    dma50 = close - 10.0 if is_bullish else close
    adx14 = 22.0 if is_bullish else 10.0
    iv_rank = 70.0 if is_bullish else 45.0
    iv_hv_ratio = 1.30 if is_bullish else 1.10
    breadth = 60.0 if is_bullish else 50.0

    return RawFeatureInput(
        symbol=snapshot.symbol,
        close=close,
        dma20=dma20,
        dma50=dma50,
        atr20=2.0,
        adx14=adx14,
        iv_rank=iv_rank,
        iv_hv_ratio=iv_hv_ratio,
        avg_daily_volume=snapshot.volume,
        option_open_interest=2000,
        option_volume=400,
        bid=2.45,
        ask=2.55,
        option_quote_age_seconds=10,
        underlying_quote_age_seconds=2,
        market_breadth_pct_above_20dma=breadth,
        earnings_date=None,
        entry_date=date(2026, 3, 10),
        dte_days=35,
    )
