from __future__ import annotations

from pathlib import Path

from options_algo_v2.services.iv_rank_history import (
    IvProxyObservation,
    append_iv_proxy_observation,
    compute_iv_rank_from_history,
    load_iv_proxy_history,
)


def test_append_and_load_iv_proxy_history(tmp_path: Path) -> None:
    path = tmp_path / "iv_proxy_history.jsonl"

    written = append_iv_proxy_observation(
        path=path,
        observation=IvProxyObservation(
            as_of_date="2026-03-01",
            symbol="XLE",
            implied_vol_proxy=0.25,
        ),
    )

    assert written is True
    rows = load_iv_proxy_history(path)
    assert len(rows) == 1
    assert rows[0].symbol == "XLE"
    assert rows[0].implied_vol_proxy == 0.25


def test_append_skips_duplicate_symbol_date(tmp_path: Path) -> None:
    path = tmp_path / "iv_proxy_history.jsonl"

    first = append_iv_proxy_observation(
        path=path,
        observation=IvProxyObservation(
            as_of_date="2026-03-01",
            symbol="XLE",
            implied_vol_proxy=0.25,
        ),
    )
    second = append_iv_proxy_observation(
        path=path,
        observation=IvProxyObservation(
            as_of_date="2026-03-01",
            symbol="XLE",
            implied_vol_proxy=0.30,
        ),
    )

    assert first is True
    assert second is False
    rows = load_iv_proxy_history(path)
    assert len(rows) == 1
    assert rows[0].implied_vol_proxy == 0.25


def test_compute_iv_rank_from_history_returns_none_with_insufficient_history(
    tmp_path: Path,
) -> None:
    path = tmp_path / "iv_proxy_history.jsonl"

    for idx in range(5):
        append_iv_proxy_observation(
            path=path,
            observation=IvProxyObservation(
                as_of_date=f"2026-03-0{idx + 1}",
                symbol="XLE",
                implied_vol_proxy=0.20 + (idx * 0.01),
            ),
        )

    rank = compute_iv_rank_from_history(
        path=path,
        symbol="XLE",
        trailing_observations=20,
    )
    assert rank is None


def test_compute_iv_rank_from_history_returns_rank_with_sufficient_history(
    tmp_path: Path,
) -> None:
    path = tmp_path / "iv_proxy_history.jsonl"

    values = [
        0.20, 0.21, 0.19, 0.18, 0.22,
        0.23, 0.24, 0.25, 0.26, 0.27,
        0.28, 0.29, 0.30, 0.31, 0.32,
        0.33, 0.34, 0.35, 0.36, 0.37,
    ]
    for idx, value in enumerate(values, start=1):
        append_iv_proxy_observation(
            path=path,
            observation=IvProxyObservation(
                as_of_date=f"2026-03-{idx:02d}",
                symbol="XLE",
                implied_vol_proxy=value,
            ),
        )

    rank = compute_iv_rank_from_history(
        path=path,
        symbol="XLE",
        trailing_observations=20,
    )

    assert rank is not None
    assert 99.0 <= rank <= 100.0


def test_compute_iv_rank_from_history_returns_50_when_range_is_flat(
    tmp_path: Path,
) -> None:
    path = tmp_path / "iv_proxy_history.jsonl"

    for idx in range(20):
        append_iv_proxy_observation(
            path=path,
            observation=IvProxyObservation(
                as_of_date=f"2026-03-{idx + 1:02d}",
                symbol="XLE",
                implied_vol_proxy=0.25,
            ),
        )

    rank = compute_iv_rank_from_history(
        path=path,
        symbol="XLE",
        trailing_observations=20,
    )

    assert rank == 50.0
