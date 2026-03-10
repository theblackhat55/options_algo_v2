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
