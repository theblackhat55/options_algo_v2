from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_trade_ideas import run_trade_ideas


def test_run_trade_ideas_returns_json_path_and_prints_trade_ideas(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPTIONS_ALGO_RUNTIME_MODE", "mock")
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)

    output_path = run_trade_ideas(
        symbols=["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "META", "XLK", "XLF", "XLE"],
    )
    path = Path(output_path)

    assert path.exists()

    payload = json.loads(path.read_text())
    assert "trade_ideas" in payload
    assert len(payload["trade_ideas"]) == 3

    captured = capsys.readouterr()
    assert "trade_idea_count=3" in captured.out
    assert "trade_idea_symbols=['AAPL', 'MSFT', 'NVDA']" in captured.out
    assert "strategy=BULL_PUT_SPREAD" in captured.out
    assert "market_regime=TREND_UP" in captured.out
    assert "iv_state=IV_RICH" in captured.out
