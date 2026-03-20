from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SupportResistanceLevel:
    price: float
    kind: str  # "support" or "resistance"
    strength: float  # 0.0 to 1.0


def identify_support_resistance(
    closes: list[float],
    *,
    lookback: int = 20,
    tolerance_pct: float = 0.5,
) -> list[SupportResistanceLevel]:
    """Identify support and resistance levels from closing prices.

    Uses a simple pivot-point approach: local minima are support,
    local maxima are resistance. Strength is based on how many times
    price touched the level within the lookback window.
    """
    if len(closes) < lookback:
        return []

    window = closes[-lookback:]
    recent_high = max(window)
    recent_low = min(window)

    levels: list[SupportResistanceLevel] = []

    # Find local minima (support) and maxima (resistance) in the window
    pivot_lows: list[float] = []
    pivot_highs: list[float] = []

    for i in range(1, len(window) - 1):
        if window[i] <= window[i - 1] and window[i] <= window[i + 1]:
            pivot_lows.append(window[i])
        if window[i] >= window[i - 1] and window[i] >= window[i + 1]:
            pivot_highs.append(window[i])

    # Cluster nearby pivots
    support_clusters = _cluster_levels(pivot_lows, tolerance_pct)
    resistance_clusters = _cluster_levels(pivot_highs, tolerance_pct)

    for level, count in support_clusters:
        strength = min(1.0, count / 3.0)  # 3+ touches = max strength
        levels.append(SupportResistanceLevel(price=level, kind="support", strength=strength))

    for level, count in resistance_clusters:
        strength = min(1.0, count / 3.0)
        levels.append(SupportResistanceLevel(price=level, kind="resistance", strength=strength))

    return sorted(levels, key=lambda lev: lev.price)


def _cluster_levels(
    prices: list[float],
    tolerance_pct: float,
) -> list[tuple[float, int]]:
    """Cluster nearby price levels and return (avg_price, touch_count)."""
    if not prices:
        return []

    sorted_prices = sorted(prices)
    clusters: list[list[float]] = [[sorted_prices[0]]]

    for price in sorted_prices[1:]:
        cluster_avg = sum(clusters[-1]) / len(clusters[-1])
        if abs(price - cluster_avg) / max(cluster_avg, 0.01) * 100 <= tolerance_pct:
            clusters[-1].append(price)
        else:
            clusters.append([price])

    return [(sum(c) / len(c), len(c)) for c in clusters]


def validate_strike_near_support_resistance(
    strike: float,
    levels: list[SupportResistanceLevel],
    *,
    kind: str = "support",
    max_distance_pct: float = 2.0,
) -> tuple[bool, float]:
    """Check if a strike is near a support or resistance level.

    Returns (is_valid, distance_pct). For put credit spreads, the
    short strike should be near support. For call debit spreads,
    the long strike should be near a resistance breakout level.
    """
    matching = [lev for lev in levels if lev.kind == kind]
    if not matching:
        return True, 0.0  # No levels = pass (no data to reject)

    best_distance = float("inf")
    for level in matching:
        if level.price > 0:
            distance_pct = abs(strike - level.price) / level.price * 100
            best_distance = min(best_distance, distance_pct)

    return best_distance <= max_distance_pct, best_distance
