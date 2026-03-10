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
    rows = build_mock_historical_rows("AAPL")

    assert rows[-1]["close"] == 135.0


def test_build_mock_historical_rows_calibrates_extended_symbol() -> None:
    rows = build_mock_historical_rows("SPY")

    assert rows[-1]["close"] == 142.0


def test_build_mock_historical_rows_calibrates_neutral_symbol() -> None:
    rows = build_mock_historical_rows("XLF")

    assert rows[-1]["close"] == 104.0
