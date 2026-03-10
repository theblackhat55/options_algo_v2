from __future__ import annotations


class DatabentoLiveClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def get_underlying_snapshot(self, symbol: str) -> dict[str, object]:
        raise NotImplementedError("Databento live client is not implemented")
