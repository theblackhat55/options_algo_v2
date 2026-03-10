from options_algo_v2.services.liquidity_filter import passes_liquidity_filter


def test_liquidity_filter_passes_for_valid_liquid_setup() -> None:
    result = passes_liquidity_filter(
        underlying_price=150.0,
        avg_daily_volume=5_000_000,
        option_open_interest=2_000,
        option_volume=500,
        bid=2.45,
        ask=2.55,
        option_quote_age_seconds=20,
        underlying_quote_age_seconds=3,
    )

    assert result.passed is True
    assert result.reasons == []


def test_liquidity_filter_rejects_multiple_failures() -> None:
    result = passes_liquidity_filter(
        underlying_price=10.0,
        avg_daily_volume=100_000,
        option_open_interest=100,
        option_volume=20,
        bid=1.00,
        ask=1.20,
        option_quote_age_seconds=120,
        underlying_quote_age_seconds=30,
    )

    assert result.passed is False
    assert len(result.reasons) >= 5


def test_liquidity_filter_rejects_invalid_quote() -> None:
    result = passes_liquidity_filter(
        underlying_price=100.0,
        avg_daily_volume=2_000_000,
        option_open_interest=1_000,
        option_volume=200,
        bid=2.00,
        ask=2.00,
        option_quote_age_seconds=10,
        underlying_quote_age_seconds=5,
    )

    assert result.passed is False
    assert "invalid bid ask quote" in result.reasons


def test_liquidity_filter_rejects_wide_spread() -> None:
    result = passes_liquidity_filter(
        underlying_price=100.0,
        avg_daily_volume=2_000_000,
        option_open_interest=1_000,
        option_volume=200,
        bid=1.00,
        ask=1.20,
        option_quote_age_seconds=10,
        underlying_quote_age_seconds=5,
    )

    assert result.passed is False
    assert "bid ask spread exceeds maximum percentage" in result.reasons
