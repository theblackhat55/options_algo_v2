from __future__ import annotations

from datetime import date

from options_algo_v2.services.options_dte_selector import (
    calculate_dte_days,
    rank_expirations_by_target_dte_distance,
    select_expirations_in_dte_window,
)


def test_calculate_dte_days_returns_day_difference() -> None:
    assert calculate_dte_days(
        expiration="2026-04-17",
        as_of_date=date(2026, 3, 10),
    ) == 38


def test_select_expirations_in_dte_window_filters_values() -> None:
    expirations = ["2026-03-20", "2026-04-17", "2026-06-19"]

    selected = select_expirations_in_dte_window(
        expirations,
        as_of_date=date(2026, 3, 10),
        min_dte=30,
        max_dte=60,
    )

    assert selected == ["2026-04-17"]


def test_rank_expirations_by_target_dte_distance_orders_nearest_first() -> None:
    expirations = ["2026-03-20", "2026-04-17", "2026-05-15"]

    ranked = rank_expirations_by_target_dte_distance(
        expirations,
        as_of_date=date(2026, 3, 10),
        target_dte=40,
    )

    assert ranked[0] == "2026-04-17"
