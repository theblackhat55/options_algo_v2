from __future__ import annotations

from datetime import date


def calculate_dte_days(
    *,
    expiration: str,
    as_of_date: date,
) -> int:
    expiration_date = date.fromisoformat(expiration)
    return (expiration_date - as_of_date).days


def select_expirations_in_dte_window(
    expirations: list[str],
    *,
    as_of_date: date,
    min_dte: int,
    max_dte: int,
) -> list[str]:
    selected: list[str] = []
    for expiration in expirations:
        dte = calculate_dte_days(expiration=expiration, as_of_date=as_of_date)
        if min_dte <= dte <= max_dte:
            selected.append(expiration)
    return selected


def rank_expirations_by_target_dte_distance(
    expirations: list[str],
    *,
    as_of_date: date,
    target_dte: int,
) -> list[str]:
    return sorted(
        expirations,
        key=lambda expiration: abs(
            calculate_dte_days(expiration=expiration, as_of_date=as_of_date)
            - target_dte
        ),
    )
