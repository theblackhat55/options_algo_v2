from options_algo_v2.services.mock_historical_rows import build_mock_historical_rows


def test_build_mock_historical_rows_returns_50_rows() -> None:
    rows = build_mock_historical_rows("AAPL")

    assert len(rows) == 50
    assert rows[0]["ts_event"] == "2026-03-01T21:00:00Z"
    assert "open" in rows[0]
    assert "high" in rows[0]
    assert "low" in rows[0]
    assert "close" in rows[0]
    assert "volume" in rows[0]
