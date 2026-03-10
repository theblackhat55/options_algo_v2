import re

from options_algo_v2.services.run_id import generate_run_id


def test_generate_run_id_uses_default_prefix() -> None:
    run_id = generate_run_id()
    assert run_id.startswith("scan_")
    assert re.fullmatch(r"scan_\d{8}T\d{6}Z", run_id)


def test_generate_run_id_allows_custom_prefix() -> None:
    run_id = generate_run_id(prefix="nightly")
    assert run_id.startswith("nightly_")
    assert re.fullmatch(r"nightly_\d{8}T\d{6}Z", run_id)
