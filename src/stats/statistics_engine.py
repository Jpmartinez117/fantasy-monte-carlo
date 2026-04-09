"""Compute summary statistics over Monte Carlo simulation results."""

import statistics
from dataclasses import dataclass
from typing import List

from src.models.player import Player
from src.simulation.monte_carlo import SimulationResults


@dataclass
class PlayerStats:
    """Per-player summary statistics derived from simulation scores.

    Percentile fields use the standard fantasy shorthand:
        p10 = floor / bust scenario
        p90 = ceiling / boom scenario
    """
    name: str
    position: str
    mean: float    # average simulated score across all trials
    std_dev: float # spread — higher means more volatile/risky
    median: float  # 50th percentile
    p10: float     # 10th percentile
    p25: float     # 25th percentile
    p75: float     # 75th percentile
    p90: float     # 90th percentile


def compute_stats(results: SimulationResults, players: List[Player]) -> List[PlayerStats]:
    """Build per-player summary statistics from raw simulation results.

    Args:
        results: SimulationResults returned by run_simulation().
        players: Original Player list (used to look up positions by name).

    Returns:
        List of PlayerStats, one entry per player.
    """
    # Build name → position map so we only iterate players once
    position_map = {p.name: p.position for p in players}

    stats_list: List[PlayerStats] = []
    for name, scores in results.scores.items():
        # Sort once here; _percentile() expects a sorted list
        sorted_scores = sorted(scores)

        stats_list.append(PlayerStats(
            name=name,
            position=position_map.get(name, "??"),
            mean=statistics.mean(scores),
            # pstdev (population) not stdev (sample) — we have the full simulation population
            std_dev=statistics.pstdev(scores),
            median=statistics.median(scores),
            p10=_percentile(sorted_scores, 10),
            p25=_percentile(sorted_scores, 25),
            p75=_percentile(sorted_scores, 75),
            p90=_percentile(sorted_scores, 90),
        ))

    return stats_list


def rank_players(stats_list: List[PlayerStats]) -> List[PlayerStats]:
    """Return players sorted by mean simulated score, highest first."""
    return sorted(stats_list, key=lambda s: s.mean, reverse=True)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _percentile(sorted_values: List[float], pct: int) -> float:
    """Return the pct-th percentile using linear interpolation.

    Args:
        sorted_values: Pre-sorted list of floats (ascending).
        pct:           Integer percentile in range [0, 100].

    Example: pct=90 on a 10,000-element list → index 8999.0 → last full value.
    """
    n = len(sorted_values)

    # Map the percentile to a fractional index along the sorted list
    idx = (pct / 100) * (n - 1)
    lo = int(idx)
    hi = lo + 1

    if hi >= n:
        # Edge case: pct=100 lands exactly on the last element
        return sorted_values[-1]

    # Weighted average of the two surrounding values
    frac = idx - lo
    return sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo])
