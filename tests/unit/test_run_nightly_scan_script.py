import json
from pathlib import Path

from scripts.run_nightly_scan import run_nightly_scan


def test_run_nightly_scan_returns_json_path() -> None:
    output_path = run_nightly_scan()
    path = Path(output_path)

    assert output_path.endswith(".json")
    assert path.exists()

    payload = json.loads(path.read_text())

    assert "summary" in payload
    assert "rejection_reason_counts" in payload["summary"]
    assert "signal_state_counts" in payload["summary"]
    assert "strategy_type_counts" in payload["summary"]
