from options_algo_v2.services.mock_historical_rows import build_mock_historical_rows


def test_build_mock_historical_rows_returns_expected_shape() -> None:
    rows = build_mock_historical_rows("AAPL")

    assert len(rows) == 50
    assert rows[0]["ts_event"] == "2026-03-01T21:00:00Z"
    assert rows[-1]["ts_event"] == "2026-03-50T21:00:00Z"
    assert "open" in rows[0]
    assert "high" in rows[0]
    assert "low" in rows[0]
    assert "close" in rows[0]
    assert "volume" in rows[0]


def test_build_mock_historical_rows_calibrates_pass_symbol() -> None:
    import math

    rows = build_mock_historical_rows("AAPL")
    # Final close = 100 + 49*0.3 + 2.0*sin(49*0.9), rounded to 2 dp
    expected = round(100.0 + 49 * 0.3 + 2.0 * math.sin(49 * 0.9), 2)
    assert rows[-1]["close"] == expected


def test_build_mock_historical_rows_calibrates_extended_symbol() -> None:
    rows = build_mock_historical_rows("SPY")
    # Final close = base[-1] + 12.0 where base[-1] = 100 + 48*0.5 = 124.0
    assert rows[-1]["close"] == 136.0


def test_build_mock_historical_rows_calibrates_neutral_symbol() -> None:
    rows = build_mock_historical_rows("XLF")

    assert rows[-1]["close"] == 104.0
