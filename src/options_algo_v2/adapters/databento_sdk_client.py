from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import ModuleType
from typing import Protocol, cast


class _DatabentoRangeResponse(Protocol):
    ...


class _DatabentoTimeseriesClient(Protocol):
    def get_range(self, **kwargs: object) -> _DatabentoRangeResponse:
        ...


class _DatabentoHistoricalClient(Protocol):
    timeseries: _DatabentoTimeseriesClient


def _load_databento_module() -> ModuleType:
    try:
        import databento
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
    lookback_days: int = 60,
) -> dict[str, object]:
    if lookback_days <= 0:
        raise ValueError("lookback_days must be positive")

    end = datetime.now(UTC).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    start = end - timedelta(days=lookback_days)

    return {
        "dataset": dataset,
        "schema": schema,
        "symbols": symbol,
        "stype_in": "raw_symbol",
        "start": start,
        "end": end,
        "limit": 100,
    }


def _record_to_dict(record: object) -> dict[str, object]:
    if isinstance(record, dict):
        return dict(record)

    if hasattr(record, "__dict__"):
        data = {
            key: value
            for key, value in vars(record).items()
            if not key.startswith("_")
        }
        if data:
            return data

    raise TypeError("unable to normalize databento record")


def _normalize_response_rows(response: object) -> list[dict[str, object]]:
    if hasattr(response, "to_list"):
        to_list = response.to_list
        if callable(to_list):
            result = to_list()
            if isinstance(result, list):
                return [dict(item) for item in result if isinstance(item, dict)]

    if hasattr(response, "to_df"):
        to_df = response.to_df
        if callable(to_df):
            df = to_df()
            if hasattr(df, "reset_index") and hasattr(df, "to_dict"):
                df = df.reset_index()
                records = df.to_dict("records")
                if isinstance(records, list):
                    return [dict(item) for item in records if isinstance(item, dict)]

    if hasattr(response, "__iter__"):
        rows: list[dict[str, object]] = []
        for item in cast(Iterable[object], response):
            try:
                rows.append(_record_to_dict(item))
            except TypeError:
                continue
        if rows:
            return rows

    raise TypeError("unable to extract rows from databento response")


@dataclass(frozen=True)
class DatabentoHistoricalClientWrapper:
    api_key: str

    def build_client(self) -> _DatabentoHistoricalClient:
        databento = _load_databento_module()
        return databento.Historical(self.api_key)

    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
        lookback_days: int = 60,
    ) -> list[dict[str, object]]:
        client = self.build_client()
        response = client.timeseries.get_range(
            **_build_get_range_kwargs(
                symbol=symbol,
                dataset=dataset,
                schema=schema,
                lookback_days=lookback_days,
            )
        )
        return _normalize_response_rows(response)

    def get_underlying_snapshot(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> dict[str, object]:
        rows = self.get_bar_rows(
            symbol=symbol,
            dataset=dataset,
            schema=schema,
            lookback_days=60,
        )

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
