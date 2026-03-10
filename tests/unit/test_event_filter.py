from datetime import date

from options_algo_v2.services.event_filter import passes_event_filter


def test_event_filter_passes_when_no_earnings_date() -> None:
    result = passes_event_filter(
        earnings_date=None,
        planned_latest_exit=date(2026, 3, 20),
    )

    assert result.passed is True
    assert result.reasons == []


def test_event_filter_rejects_when_earnings_before_exit() -> None:
    result = passes_event_filter(
        earnings_date=date(2026, 3, 18),
        planned_latest_exit=date(2026, 3, 20),
    )

    assert result.passed is False
    assert "earnings event occurs before planned exit" in result.reasons


def test_event_filter_rejects_when_earnings_on_exit_date() -> None:
    result = passes_event_filter(
        earnings_date=date(2026, 3, 20),
        planned_latest_exit=date(2026, 3, 20),
    )

    assert result.passed is False


def test_event_filter_passes_when_earnings_after_exit() -> None:
    result = passes_event_filter(
        earnings_date=date(2026, 3, 21),
        planned_latest_exit=date(2026, 3, 20),
    )

    assert result.passed is True
