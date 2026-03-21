from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class OptionsContextRow:
    symbol: str
    as_of_utc: str
    source_provider: str

    contract_count: int | None = None
    expiration_count: int | None = None
    call_count: int | None = None
    put_count: int | None = None

    call_oi_total: int | None = None
    put_oi_total: int | None = None
    call_volume_total: int | None = None
    put_volume_total: int | None = None
    pcr_oi: float | None = None
    pcr_volume: float | None = None

    atm_iv: float | None = None
    expected_move_1d_pct: float | None = None
    expected_move_1w_pct: float | None = None
    expected_move_30d_pct: float | None = None

    skew_25d_put_call_ratio: float | None = None
    skew_25d_put_call_spread: float | None = None

    nonzero_bid_ask_count: int | None = None
    nonzero_open_interest_count: int | None = None
    nonzero_delta_count: int | None = None
    nonzero_iv_count: int | None = None

    nonzero_bid_ask_ratio: float | None = None
    nonzero_open_interest_ratio: float | None = None
    nonzero_delta_ratio: float | None = None
    nonzero_iv_ratio: float | None = None

    options_summary_regime: str | None = None

    confidence_score: float = 0.0
    confidence_reasons: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OptionsContextSnapshot:
    run_id: str
    generated_at_utc: str
    source_watchlist: str
    symbol_count: int
    rows: list[OptionsContextRow]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "generated_at_utc": self.generated_at_utc,
            "source_watchlist": self.source_watchlist,
            "symbol_count": self.symbol_count,
            "rows": [row.to_dict() for row in self.rows],
        }
