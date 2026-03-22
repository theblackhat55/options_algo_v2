from __future__ import annotations

import json
from unittest.mock import patch

from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from scripts.build_options_context_snapshot import build_options_context_snapshot


class _FakeProvider:
    def get_chain(self, symbol: str) -> OptionsChainSnapshot:
        return OptionsChainSnapshot(
            symbol=symbol,
            as_of="2026-03-21T00:00:00Z",
            source="test_provider",
            quotes=[
                OptionQuote(
                    symbol=symbol,
                    option_symbol=f"{symbol}_C",
                    expiration="2026-03-28",
                    strike=100.0,
                    option_type="CALL",
                    bid=5.0,
                    ask=5.0,
                    mid=5.0,
                    delta=0.25,
                    implied_volatility=0.20,
                    open_interest=100,
                    volume=50,
                ),
                OptionQuote(
                    symbol=symbol,
                    option_symbol=f"{symbol}_P",
                    expiration="2026-03-28",
                    strike=100.0,
                    option_type="PUT",
                    bid=6.0,
                    ask=6.0,
                    mid=6.0,
                    delta=-0.25,
                    implied_volatility=0.24,
                    open_interest=120,
                    volume=60,
                ),
                OptionQuote(
                    symbol=symbol,
                    option_symbol=f"{symbol}_C30",
                    expiration="2026-04-20",
                    strike=100.0,
                    option_type="CALL",
                    bid=8.0,
                    ask=8.0,
                    mid=8.0,
                    delta=0.50,
                    implied_volatility=0.21,
                    open_interest=100,
                    volume=40,
                ),
                OptionQuote(
                    symbol=symbol,
                    option_symbol=f"{symbol}_P30",
                    expiration="2026-04-20",
                    strike=100.0,
                    option_type="PUT",
                    bid=9.0,
                    ask=9.0,
                    mid=9.0,
                    delta=-0.50,
                    implied_volatility=0.25,
                    open_interest=130,
                    volume=70,
                ),
            ],
        )


def test_build_options_context_snapshot_upserts_to_sqlite(tmp_path) -> None:
    watchlist_path = tmp_path / "watchlist.json"
    db_path = tmp_path / "market_history_watchlist60.db"

    watchlist_path.write_text(
        json.dumps(
            {
                "rows": [
                    {"symbol": "SPY", "close": 100.0},
                    {"symbol": "QQQ", "close": 100.0},
                ]
            }
        ),
        encoding="utf-8",
    )

    with patch(
        "scripts.build_options_context_snapshot.build_options_chain_provider",
        return_value=_FakeProvider(),
    ), patch(
        "scripts.build_options_context_snapshot.get_options_chain_provider_name",
        return_value="fake_provider",
    ), patch(
        "scripts.build_options_context_snapshot.get_options_chain_provider_source",
        return_value="fake_source",
    ), patch(
        "scripts.build_options_context_snapshot.upsert_options_context_snapshots",
        return_value=str(db_path),
    ) as mock_upsert:
        output = build_options_context_snapshot(
            str(watchlist_path),
            db_path=str(db_path),
        )

    assert output == str(db_path)
    mock_upsert.assert_called_once()
    call_kwargs = mock_upsert.call_args.kwargs
    assert call_kwargs["db_path"] == str(db_path)
    assert len(call_kwargs["snapshots"]) == 2
    assert {snapshot.symbol for snapshot in call_kwargs["snapshots"]} == {"SPY", "QQQ"}
