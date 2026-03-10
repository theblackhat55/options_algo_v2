from __future__ import annotations

from dataclasses import dataclass
from types import ModuleType


def _load_databento_module() -> ModuleType:
    try:
        import databento  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("databento package is not installed") from exc

    return databento


@dataclass(frozen=True)
class DatabentoHistoricalClientWrapper:
    api_key: str

    def build_client(self) -> object:
        databento = _load_databento_module()
        return databento.Historical(api_key=self.api_key)

    def get_underlying_snapshot(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
    ) -> dict[str, object]:
        _client = self.build_client()
        raise NotImplementedError("Databento SDK wrapper fetch is not implemented")
