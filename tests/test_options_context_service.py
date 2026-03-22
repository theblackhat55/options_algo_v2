from __future__ import annotations

import pytest

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.services.options_context_service import (
    compute_expected_moves,
    compute_options_context_snapshot,
    compute_positioning_metrics,
    compute_skew_metrics,
)


def _quote(
    *,
    symbol: str = "SPY",
    option_symbol: str,
    expiration: str,
    strike: float,
    option_type: str,
    mid: float,
    delta: float | None,
    implied_volatility: float | None,
    open_interest: int = 0,
    volume: int = 0,
) -> OptionQuote:
    return OptionQuote(
        symbol=symbol,
        option_symbol=option_symbol,
        expiration=expiration,
        strike=strike,
        option_type=option_type,
        bid=mid,
        ask=mid,
        mid=mid,
        delta=delta,
        implied_volatility=implied_volatility,
        open_interest=open_interest,
        volume=volume,
    )


def test_compute_positioning_metrics_sums_totals_and_pcrs() -> None:
    chain = OptionsChainSnapshot(
        symbol="SPY",
        quotes=[
            _quote(
                option_symbol="C1",
                expiration="2026-03-28",
                strike=600.0,
                option_type="CALL",
                mid=5.0,
                delta=0.4,
                implied_volatility=0.20,
                open_interest=100,
                volume=25,
            ),
            _quote(
                option_symbol="P1",
                expiration="2026-03-28",
                strike=600.0,
                option_type="PUT",
                mid=6.0,
                delta=-0.4,
                implied_volatility=0.24,
                open_interest=150,
                volume=50,
            ),
        ],
        as_of="2026-03-21T00:00:00Z",
        source="test",
    )

    metrics = compute_positioning_metrics(chain=chain)

    assert metrics.call_oi_total == 100
    assert metrics.put_oi_total == 150
    assert metrics.call_volume_total == 25
    assert metrics.put_volume_total == 50
    assert metrics.pcr_oi == 1.5
    assert metrics.pcr_volume == 2.0


def test_compute_skew_metrics_uses_25_delta_proxy() -> None:
    chain = OptionsChainSnapshot(
        symbol="SPY",
        quotes=[
            _quote(
                option_symbol="P25",
                expiration="2026-04-20",
                strike=570.0,
                option_type="PUT",
                mid=7.0,
                delta=-0.24,
                implied_volatility=0.30,
                open_interest=100,
                volume=10,
            ),
            _quote(
                option_symbol="C25",
                expiration="2026-04-20",
                strike=630.0,
                option_type="CALL",
                mid=8.0,
                delta=0.26,
                implied_volatility=0.20,
                open_interest=100,
                volume=10,
            ),
        ],
        as_of="2026-03-21T00:00:00Z",
        source="test",
    )

    skew = compute_skew_metrics(spot_price=600.0, chain=chain)

    assert skew.skew_25d_put_call_ratio == pytest.approx(1.5)
    assert skew.skew_25d_put_call_spread == pytest.approx(0.10)


def test_compute_options_context_snapshot_populates_core_fields() -> None:
    chain = OptionsChainSnapshot(
        symbol="SPY",
        quotes=[
            _quote(
                option_symbol="C1D",
                expiration="2026-03-22",
                strike=600.0,
                option_type="CALL",
                mid=4.0,
                delta=0.50,
                implied_volatility=0.18,
                open_interest=200,
                volume=100,
            ),
            _quote(
                option_symbol="P1D",
                expiration="2026-03-22",
                strike=600.0,
                option_type="PUT",
                mid=5.0,
                delta=-0.50,
                implied_volatility=0.19,
                open_interest=250,
                volume=125,
            ),
            _quote(
                option_symbol="C1W",
                expiration="2026-03-28",
                strike=600.0,
                option_type="CALL",
                mid=10.0,
                delta=0.50,
                implied_volatility=0.20,
                open_interest=300,
                volume=80,
            ),
            _quote(
                option_symbol="P1W",
                expiration="2026-03-28",
                strike=600.0,
                option_type="PUT",
                mid=11.0,
                delta=-0.50,
                implied_volatility=0.22,
                open_interest=350,
                volume=90,
            ),
            _quote(
                option_symbol="P25",
                expiration="2026-04-20",
                strike=570.0,
                option_type="PUT",
                mid=14.0,
                delta=-0.25,
                implied_volatility=0.29,
                open_interest=400,
                volume=70,
            ),
            _quote(
                option_symbol="C25",
                expiration="2026-04-20",
                strike=630.0,
                option_type="CALL",
                mid=13.0,
                delta=0.25,
                implied_volatility=0.21,
                open_interest=380,
                volume=60,
            ),
            _quote(
                option_symbol="C30ATM",
                expiration="2026-04-20",
                strike=600.0,
                option_type="CALL",
                mid=18.0,
                delta=0.51,
                implied_volatility=0.23,
                open_interest=500,
                volume=120,
            ),
            _quote(
                option_symbol="P30ATM",
                expiration="2026-04-20",
                strike=600.0,
                option_type="PUT",
                mid=19.0,
                delta=-0.49,
                implied_volatility=0.24,
                open_interest=520,
                volume=130,
            ),
            _quote(
                option_symbol="C30OTM",
                expiration="2026-04-20",
                strike=620.0,
                option_type="CALL",
                mid=11.0,
                delta=0.35,
                implied_volatility=0.22,
                open_interest=150,
                volume=30,
            ),
            _quote(
                option_symbol="P30OTM",
                expiration="2026-04-20",
                strike=580.0,
                option_type="PUT",
                mid=12.0,
                delta=-0.35,
                implied_volatility=0.26,
                open_interest=175,
                volume=35,
            ),
        ],
        as_of="2026-03-21T00:00:00Z",
        source="polygon",
    )

    snapshot = compute_options_context_snapshot(
        symbol="SPY",
        as_of_utc="2026-03-21T00:00:00Z",
        spot_price=600.0,
        chain=chain,
        source_provider="polygon",
    )

    assert snapshot.symbol == "SPY"
    assert snapshot.source_provider == "polygon"
    assert snapshot.expected_move_1d_pct == (4.0 + 5.0) / 600.0
    assert snapshot.expected_move_1w_pct == (10.0 + 11.0) / 600.0
    assert snapshot.expected_move_30d_pct == (18.0 + 19.0) / 600.0
    assert snapshot.pcr_oi is not None
    assert snapshot.contract_count == 10
    assert snapshot.expiration_count == 3
    assert snapshot.atm_iv is not None
    assert snapshot.nonzero_bid_ask_ratio == pytest.approx(1.0)
    assert snapshot.nonzero_open_interest_ratio == pytest.approx(1.0)
    assert snapshot.nonzero_delta_ratio == pytest.approx(1.0)
    assert snapshot.nonzero_iv_ratio == pytest.approx(1.0)
    assert snapshot.options_summary_regime in {"tradable", "call_heavy_liquid", "put_heavy_liquid"}
    assert snapshot.pcr_volume is not None
    assert snapshot.skew_25d_put_call_ratio == pytest.approx(0.29 / 0.21)
    assert snapshot.skew_25d_put_call_spread == pytest.approx(0.29 - 0.21)
    assert snapshot.confidence_score > 0.0


def test_compute_expected_moves_returns_nulls_when_spot_missing() -> None:
    chain = OptionsChainSnapshot(
        symbol="SPY",
        quotes=[],
        as_of="2026-03-21T00:00:00Z",
        source="test",
    )

    moves = compute_expected_moves(spot_price=None, chain=chain)

    assert moves.expected_move_1d_pct is None
    assert moves.expected_move_1w_pct is None
    assert moves.expected_move_30d_pct is None
