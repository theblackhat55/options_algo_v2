from options_algo_v2.domain.underlying_data import UnderlyingSnapshot
from options_algo_v2.services.sample_feature_factory import (
    build_sample_raw_features_from_snapshot,
)


def test_build_sample_raw_features_from_snapshot_for_bullish_symbol() -> None:
    snapshot = UnderlyingSnapshot(
        symbol="AAPL",
        close=210.0,
        volume=5_000_000,
        timestamp="2026-03-10T21:00:00Z",
    )

    raw = build_sample_raw_features_from_snapshot(snapshot)

    assert raw.symbol == "AAPL"
    assert raw.close == 210.0
    assert raw.dma20 == 205.0
    assert raw.dma50 == 200.0
    assert raw.adx14 == 22.0
    assert raw.iv_rank == 70.0


def test_build_sample_raw_features_from_snapshot_for_neutral_symbol() -> None:
    snapshot = UnderlyingSnapshot(
        symbol="IBM",
        close=100.0,
        volume=2_000_000,
        timestamp="2026-03-10T21:00:00Z",
    )

    raw = build_sample_raw_features_from_snapshot(snapshot)

    assert raw.symbol == "IBM"
    assert raw.dma20 == 100.0
    assert raw.dma50 == 100.0
    assert raw.adx14 == 10.0
    assert raw.iv_rank == 45.0
