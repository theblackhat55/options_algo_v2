from __future__ import annotations

from datetime import date

from options_algo_v2.domain.raw_features import RawFeatureInput
from options_algo_v2.domain.underlying_data import UnderlyingSnapshot


def build_sample_raw_features_from_snapshot(
    snapshot: UnderlyingSnapshot,
) -> RawFeatureInput:
    pass_symbols = {"AAPL", "MSFT", "NVDA"}
    extended_symbols = {"META", "SPY", "QQQ"}

    symbol = snapshot.symbol
    close = snapshot.close

    if symbol in pass_symbols:
        dma20 = close - 2.0
        dma50 = close - 5.0
        adx14 = 35.0
        iv_rank = 70.0
        iv_hv_ratio = 1.45
        breadth = 65.0
        atr20 = 2.0
    elif symbol in extended_symbols:
        dma20 = close - 5.0
        dma50 = close - 10.0
        adx14 = 35.0
        iv_rank = 70.0
        iv_hv_ratio = 1.45
        breadth = 65.0
        atr20 = 2.0
    else:
        dma20 = close
        dma50 = close
        adx14 = 10.0
        iv_rank = 45.0
        iv_hv_ratio = 1.10
        breadth = 50.0
        atr20 = 2.0

    return RawFeatureInput(
        symbol=symbol,
        close=close,
        dma20=dma20,
        dma50=dma50,
        atr20=atr20,
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
        rsi14=50.0,
        five_day_return=0.0,
    )
