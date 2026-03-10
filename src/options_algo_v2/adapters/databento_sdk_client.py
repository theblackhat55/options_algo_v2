from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from types import ModuleType
from typing import Protocol, cast


class _DatabentoRangeResponse(Protocol):
    def to_list(self) -> list[dict[str, object]]:
        ...


class _DatabentoTimeseriesClient(Protocol):
    def get_range(self, **kwargs: object) -> _DatabentoRangeResponse:
        ...


class _DatabentoHistoricalClient(Protocol):
    timeseries: _DatabentoTimeseriesClient


def _load_databento_module() -> ModuleType:
    try:
        import databento  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("databento package is not installed") from exc

    return databento


def _require_row_key(row: dict[str, object], key: str) -> object:
    if key not in row:
        raise ValueError(f"missing '{key}' in databento row")
    return row[key]


def _parse_positive_close(value: object) -> float:
    try:
        parsed = float(cast(float | int | str, value))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid 'close' value in databento row") from exc

    if parsed <= 0:
        raise ValueError("close must be positive in databento row")

    return parsed


def _parse_non_negative_volume(value: object) -> float:
    try:
        parsed = float(cast(float | int | str, value))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid 'volume' value in databento row") from exc

    if parsed < 0:
        raise ValueError("volume cannot be negative in databento row")

    return parsed


def _parse_timestamp(value: object) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            normalized = value.replace(tzinfo=UTC)
        else:
            normalized = value.astimezone(UTC)
        return normalized.isoformat().replace("+00:00", "Z")

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise ValueError("invalid 'ts_event' value in databento row")

        normalized_input = raw.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized_input)
        except ValueError as exc:
            raise ValueError("invalid 'ts_event' value in databento row") from exc

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        else:
            parsed = parsed.astimezone(UTC)

        return parsed.isoformat().replace("+00:00", "Z")

    raise ValueError("invalid 'ts_event' value in databento row")


def _build_get_range_kwargs(
    *,
    symbol: str,
    dataset: str,
    schema: str,
) -> dict[str, object]:
    return {
        "dataset": dataset,
        "schema": schema,
        "symbols": symbol,
        "stype_in": "raw_symbol",
        "limit": 100,
    }


@dataclass(frozen=True)
class DatabentoHistoricalClientWrapper:
    api_key: str

    def build_client(self) -> _DatabentoHistoricalClient:
        databento = _load_databento_module()
        return databento.Historical(api_key=self.api_key)

    def get_underlying_snapshot(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> dict[str, object]:
        client = self.build_client()
        response = client.timeseries.get_range(
            **_build_get_range_kwargs(
                symbol=symbol,
                dataset=dataset,
                schema=schema,
            )
        )
        rows = response.to_list()

        if not rows:
            raise ValueError(f"no databento rows returned for symbol={symbol}")

        last_row = rows[-1]
        close_value = _require_row_key(last_row, "close")
        volume_value = _require_row_key(last_row, "volume")
        timestamp_value = _require_row_key(last_row, "ts_event")

        return {
            "close": _parse_positive_close(close_value),
            "volume": _parse_non_negative_volume(volume_value),
            "timestamp": _parse_timestamp(timestamp_value),
        }
