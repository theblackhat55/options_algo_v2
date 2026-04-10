from __future__ import annotations

from typing import Protocol


class HistoricalRowProvider(Protocol):
    def get_bar_rows(
        self,
        *,
        symbol: str,
        dataset: str,
        schema: str,
        end_date: str | None = None,
    ) -> list[dict[str, object]]:
        ...
