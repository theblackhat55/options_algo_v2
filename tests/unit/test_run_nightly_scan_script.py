from pathlib import Path

from scripts.run_nightly_scan import run_nightly_scan


def test_run_nightly_scan_returns_json_path() -> None:
    output_path = run_nightly_scan()

    assert output_path.endswith(".json")
    assert Path(output_path).exists()
