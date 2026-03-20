from options_algo_v2.services.support_resistance import (
    SupportResistanceLevel,
    identify_support_resistance,
    validate_strike_near_support_resistance,
)


def test_identify_support_resistance_returns_levels() -> None:
    # Oscillating prices with clear support at ~95 and resistance at ~105
    closes = (
        [100, 103, 105, 103, 100, 97, 95, 97, 100, 103]
        + [105, 103, 100, 97, 95, 97, 100, 103, 105, 103]
    )
    levels = identify_support_resistance(closes, lookback=20)
    assert len(levels) > 0
    kinds = {lev.kind for lev in levels}
    assert "support" in kinds
    assert "resistance" in kinds


def test_identify_support_resistance_empty_for_short_history() -> None:
    levels = identify_support_resistance([100, 101, 102], lookback=20)
    assert levels == []


def test_validate_strike_near_support() -> None:
    levels = [
        SupportResistanceLevel(price=95.0, kind="support", strength=0.8),
        SupportResistanceLevel(price=105.0, kind="resistance", strength=0.7),
    ]
    is_valid, dist = validate_strike_near_support_resistance(
        95.5, levels, kind="support", max_distance_pct=2.0
    )
    assert is_valid is True
    assert dist < 1.0


def test_validate_strike_far_from_support() -> None:
    levels = [
        SupportResistanceLevel(price=95.0, kind="support", strength=0.8),
    ]
    is_valid, dist = validate_strike_near_support_resistance(
        88.0, levels, kind="support", max_distance_pct=2.0
    )
    assert is_valid is False
    assert dist > 2.0


def test_validate_strike_passes_when_no_levels() -> None:
    is_valid, dist = validate_strike_near_support_resistance(
        100.0, [], kind="support", max_distance_pct=2.0
    )
    assert is_valid is True
    assert dist == 0.0
