from options_algo_v2.services.candidate_ranker import score_candidate


def test_score_candidate_full_score_without_penalty() -> None:
    score = score_candidate(
        regime_fit=True,
        directional_fit=True,
        iv_fit=True,
        liquidity_fit=True,
        expected_move_fit=True,
        is_extended=False,
    )

    assert score == 100.0


def test_score_candidate_applies_extension_penalty() -> None:
    score = score_candidate(
        regime_fit=True,
        directional_fit=True,
        iv_fit=True,
        liquidity_fit=True,
        expected_move_fit=True,
        is_extended=True,
    )

    assert score == 90.0


def test_score_candidate_partial_score() -> None:
    score = score_candidate(
        regime_fit=True,
        directional_fit=False,
        iv_fit=True,
        liquidity_fit=False,
        expected_move_fit=True,
        is_extended=False,
    )

    assert score == 55.0


def test_score_candidate_zero_score() -> None:
    score = score_candidate(
        regime_fit=False,
        directional_fit=False,
        iv_fit=False,
        liquidity_fit=False,
        expected_move_fit=False,
        is_extended=False,
    )

    assert score == 0.0


def test_score_candidate_continuous_inputs() -> None:
    """Continuous inputs override booleans for finer scoring."""
    score = score_candidate(
        regime_fit=True,
        directional_fit=True,
        iv_fit=True,
        liquidity_fit=True,
        expected_move_fit=True,
        is_extended=False,
        adx=29.0,          # halfway in [18, 40] -> 0.5 * 25 = 12.5
        iv_ratio=1.25,     # halfway in [1.0, 1.5] -> 0.5 * 20 = 10
        breadth_distance=7.5,  # halfway in [0, 15] -> 0.5 * 20 = 10
        momentum_score=0.5,    # 0.5 * 15 = 7.5
    )
    # 10 + 12.5 + 10 + 20 (liquidity still boolean) + 7.5 = 60
    assert score == 60.0


def test_score_candidate_continuous_strong_signals() -> None:
    """Strong continuous signals score near max."""
    score = score_candidate(
        regime_fit=True,
        directional_fit=True,
        iv_fit=True,
        liquidity_fit=True,
        expected_move_fit=True,
        is_extended=False,
        adx=40.0,
        iv_ratio=1.5,
        breadth_distance=15.0,
        momentum_score=1.0,
    )
    assert score == 100.0
