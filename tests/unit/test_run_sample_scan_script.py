from scripts.run_sample_scan import build_sample_decisions


def test_build_sample_decisions_returns_expected_results() -> None:
    decisions = build_sample_decisions()

    assert len(decisions) == 2
    assert decisions[0].candidate.symbol == "AAPL"
    assert decisions[0].final_passed is True
    assert decisions[1].candidate.symbol == "SPY"
    assert decisions[1].final_passed is False
