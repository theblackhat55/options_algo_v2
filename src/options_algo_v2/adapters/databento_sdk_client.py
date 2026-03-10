from __future__ import annotations

from dataclasses import dataclass
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
            dataset=dataset,
            schema=schema,
            symbols=symbol,
        )
        rows = response.to_list()

        if not rows:
            raise ValueError(f"no databento rows returned for symbol={symbol}")

        last_row = rows[-1]
        close_value = cast(float | int | str, last_row["close"])
        volume_value = cast(float | int | str, last_row["volume"])

        return {
            "close": float(close_value),
            "volume": float(volume_value),
            "timestamp": str(last_row["ts_event"]),
        }
