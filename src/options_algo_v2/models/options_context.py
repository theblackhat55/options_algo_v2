from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExpectedMoveSnapshot:
    expected_move_1d_pct: float | None = None
    expected_move_1w_pct: float | None = None
    expected_move_30d_pct: float | None = None


@dataclass(frozen=True)
class SkewSnapshot:
    skew_25d_put_call_ratio: float | None = None
    skew_25d_put_call_spread: float | None = None


@dataclass(frozen=True)
class PositioningSnapshot:
    call_oi_total: int | None = None
    put_oi_total: int | None = None
    call_volume_total: int | None = None
    put_volume_total: int | None = None
    pcr_oi: float | None = None
    pcr_volume: float | None = None


@dataclass(frozen=True)
class GammaStructureSnapshot:
    max_gamma_strike: float | None = None
    gamma_flip_estimate: float | None = None
    distance_to_gamma_flip_pct: float | None = None
    gex_per_1pct_move: float | None = None
    nearest_expiry_gamma_pct: float | None = None


@dataclass(frozen=True)
class OptionsContextSnapshot:
    symbol: str
    as_of_utc: str
    spot_price: float | None

    contract_count: int | None = None
    expiration_count: int | None = None
    atm_iv: float | None = None

    expected_move_1d_pct: float | None = None
    expected_move_1w_pct: float | None = None
    expected_move_30d_pct: float | None = None

    skew_25d_put_call_ratio: float | None = None
    skew_25d_put_call_spread: float | None = None

    call_oi_total: int | None = None
    put_oi_total: int | None = None
    call_volume_total: int | None = None
    put_volume_total: int | None = None
    pcr_oi: float | None = None
    pcr_volume: float | None = None

    nonzero_bid_ask_ratio: float | None = None
    nonzero_open_interest_ratio: float | None = None
    nonzero_delta_ratio: float | None = None
    nonzero_iv_ratio: float | None = None

    max_gamma_strike: float | None = None
    gamma_flip_estimate: float | None = None
    distance_to_gamma_flip_pct: float | None = None
    gex_per_1pct_move: float | None = None
    nearest_expiry_gamma_pct: float | None = None

    options_flow_regime: str | None = None
    options_summary_regime: str | None = None

    confidence_score: float = 0.0
    confidence_reasons: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    source_provider: str = ""
