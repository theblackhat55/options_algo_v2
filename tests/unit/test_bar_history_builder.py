import pytest

from options_algo_v2.domain.bar_data import BarData
from options_algo_v2.services.bar_history_builder import build_bar_data_history


def test_build_bar_data_history_returns_expected_bars() -> None:
    rows = [
        {
            "ts_event": "2026-03-10T20:59:00Z",
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "volume": 1_000_000,
        },
        {
            "ts_event": "2026-03-10T21:00:00Z",
            "open": 101.0,
            "high": 103.0,
            "low": 100.0,
            "close": 102.0,
            "volume": 1_250_000,
        },
    ]

    bars = build_bar_data_history(rows)

    assert bars == [
        BarData(
            timestamp="2026-03-10T20:59:00Z",
            open=100.0,
            high=102.0,
            low=99.0,
            close=101.0,
            volume=1_000_000.0,
        ),
        BarData(
            timestamp="2026-03-10T21:00:00Z",
            open=101.0,
            high=103.0,
            low=100.0,
            close=102.0,
            volume=1_250_000.0,
        ),
    ]


def test_build_bar_data_history_raises_for_empty_rows() -> None:
    with pytest.raises(ValueError, match="no rows provided"):
        build_bar_data_history([])


def test_build_bar_data_history_raises_when_field_missing() -> None:
    rows = [
        {
            "ts_event": "2026-03-10T21:00:00Z",
            "open": 101.0,
            "high": 103.0,
            "low": 100.0,
            "close": 102.0,
        }
    ]

    with pytest.raises(ValueError, match="missing 'volume'"):
        build_bar_data_history(rows)


def test_build_bar_data_history_raises_when_high_below_low() -> None:
    rows = [
        {
            "ts_event": "2026-03-10T21:00:00Z",
            "open": 101.0,
            "high": 99.0,
            "low": 100.0,
            "close": 102.0,
            "volume": 1_000_000,
        }
    ]

    with pytest.raises(ValueError, match="high cannot be below low"):
        build_bar_data_history(rows)


def test_build_bar_data_history_raises_when_ohlc_non_positive() -> None:
    rows = [
        {
            "ts_event": "2026-03-10T21:00:00Z",
            "open": 0.0,
            "high": 103.0,
            "low": 100.0,
            "close": 102.0,
            "volume": 1_000_000,
        }
    ]

    with pytest.raises(ValueError, match="ohlc values must be positive"):
        build_bar_data_history(rows)


def test_build_bar_data_history_raises_when_volume_negative() -> None:
    rows = [
        {
            "ts_event": "2026-03-10T21:00:00Z",
            "open": 101.0,
            "high": 103.0,
            "low": 100.0,
            "close": 102.0,
            "volume": -1.0,
        }
    ]

    with pytest.raises(ValueError, match="volume cannot be negative"):
        build_bar_data_history(rows)
