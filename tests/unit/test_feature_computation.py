from options_algo_v2.domain.bar_data import BarData
from options_algo_v2.services.feature_computation import (
    compute_atr20,
    compute_sma,
    compute_underlying_features,
)


def _make_bar(
    *,
    day: int,
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: float = 1_000_000,
) -> BarData:
    return BarData(
        timestamp=f"2026-01-{day:02d}T21:00:00Z",
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def test_compute_sma_returns_expected_average() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]

    assert compute_sma(values, 3) == 4.0


def test_compute_sma_raises_for_insufficient_values() -> None:
    try:
        compute_sma([1.0, 2.0], 3)
    except ValueError as exc:
        assert str(exc) == "need at least 3 values to compute SMA"
    else:
        raise AssertionError("expected ValueError for insufficient values")


def test_compute_atr20_returns_expected_value_for_constant_ranges() -> None:
    bars = []
    close = 100.0

    for day in range(1, 22):
        bars.append(
            _make_bar(
                day=day,
                open_price=close,
                high=close + 2.0,
                low=close - 2.0,
                close=close + 1.0,
            )
        )
        close += 1.0

    atr20 = compute_atr20(bars)

    assert atr20 == 4.0


def test_compute_atr20_raises_for_insufficient_bars() -> None:
    bars = [
        _make_bar(
            day=day,
            open_price=100.0,
            high=102.0,
            low=98.0,
            close=101.0,
        )
        for day in range(1, 21)
    ]

    try:
        compute_atr20(bars)
    except ValueError as exc:
        assert str(exc) == "need at least 21 bars to compute ATR20"
    else:
        raise AssertionError("expected ValueError for insufficient ATR bars")


def test_compute_underlying_features_returns_expected_values() -> None:
    bars = []

    for index in range(50):
        close = float(index + 1)
        bars.append(
            _make_bar(
                day=(index % 28) + 1,
                open_price=close,
                high=close + 2.0,
                low=close - 2.0,
                close=close,
            )
        )

    features = compute_underlying_features(bars)

    assert features.close == 50.0
    assert features.dma20 == 40.5
    assert features.dma50 == 25.5
    assert features.atr20 == 4.0


def test_compute_underlying_features_raises_for_insufficient_bars() -> None:
    bars = [
        _make_bar(
            day=(index % 28) + 1,
            open_price=100.0,
            high=102.0,
            low=98.0,
            close=100.0,
        )
        for index in range(49)
    ]

    try:
        compute_underlying_features(bars)
    except ValueError as exc:
        assert str(exc) == "need at least 50 bars to compute underlying features"
    else:
        raise AssertionError("expected ValueError for insufficient feature bars")
