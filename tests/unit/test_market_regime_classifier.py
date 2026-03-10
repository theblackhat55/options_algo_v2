from options_algo_v2.classifiers.market_regime import classify_market_regime
from options_algo_v2.domain.enums import MarketRegime
from options_algo_v2.domain.features import MarketRegimeFeatures


def test_classify_trend_up() -> None:
    features = MarketRegimeFeatures(
        spy_close_above_20dma=True,
        spy_20dma_above_50dma=True,
        spy_close_below_20dma=False,
        spy_20dma_below_50dma=False,
        breadth_pct_above_20dma=65.0,
        vix_defensive=False,
    )
    assert classify_market_regime(features) == MarketRegime.TREND_UP


def test_classify_trend_down() -> None:
    features = MarketRegimeFeatures(
        spy_close_above_20dma=False,
        spy_20dma_above_50dma=False,
        spy_close_below_20dma=True,
        spy_20dma_below_50dma=True,
        breadth_pct_above_20dma=35.0,
        vix_defensive=False,
    )
    assert classify_market_regime(features) == MarketRegime.TREND_DOWN


def test_classify_risk_off() -> None:
    features = MarketRegimeFeatures(
        spy_close_above_20dma=True,
        spy_20dma_above_50dma=True,
        spy_close_below_20dma=False,
        spy_20dma_below_50dma=False,
        breadth_pct_above_20dma=70.0,
        vix_defensive=True,
    )
    assert classify_market_regime(features) == MarketRegime.RISK_OFF


def test_classify_range_unclear() -> None:
    features = MarketRegimeFeatures(
        spy_close_above_20dma=True,
        spy_20dma_above_50dma=False,
        spy_close_below_20dma=False,
        spy_20dma_below_50dma=False,
        breadth_pct_above_20dma=50.0,
        vix_defensive=False,
    )
    assert classify_market_regime(features) == MarketRegime.RANGE_UNCLEAR
