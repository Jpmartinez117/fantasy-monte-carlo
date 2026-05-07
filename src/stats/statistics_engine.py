"""Compute summary statistics over Monte Carlo simulation results."""

import statistics
from dataclasses import dataclass
from typing import List

from src.models.player import Player
from src.simulation.monte_carlo import SimulationResults


@dataclass
class H2HResult:
    """Outcome of a head-to-head roster simulation.

    All percentages are out of 100 (e.g. 63.4 means 63.4%).
    avg_margin is positive when Team A has the advantage.
    """
    team_a_win_pct: float
    team_b_win_pct: float
    tie_pct: float
    avg_margin: float   # mean(team_a_total - team_b_total) across all simulations
    team_a_mean: float  # average total points for team A per simulation
    team_b_mean: float  # average total points for team B per simulation


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


def head_to_head(
    results: SimulationResults,
    team_a_names: List[str],
    team_b_names: List[str],
) -> H2HResult:
    """Compare two rosters across every simulation and return win probabilities.

    For each simulation trial we sum each team's individual player scores to
    get a total team score, then tally wins, losses, and ties.

    Args:
        results:       SimulationResults from run_simulation() containing all players.
        team_a_names:  Player names that make up Team A's roster.
        team_b_names:  Player names that make up Team B's roster.

    Returns:
        H2HResult with win percentages and average scoring margin.

    Raises:
        ValueError: If either roster is empty, contains a duplicate player,
                    or names a player not present in the simulation results.
    """
    # Reject empty rosters — a "team" with no players has no meaningful
    # win probability and would silently produce a 100%/0% degenerate
    # result without this check.
    if not team_a_names:
        raise ValueError("Team A roster cannot be empty")
    if not team_b_names:
        raise ValueError("Team B roster cannot be empty")

    # Reject within-team duplicates.  A typo like splitting "Smith, Jr."
    # on the comma in the CLI could otherwise count one player twice and
    # silently inflate that team's score.  Cross-team duplicates (same
    # player on both sides) are still allowed — that's a degenerate but
    # well-defined scenario the simulator handles correctly.
    if len(set(team_a_names)) != len(team_a_names):
        raise ValueError("Team A has duplicate players")
    if len(set(team_b_names)) != len(team_b_names):
        raise ValueError("Team B has duplicate players")

    # Validate that every name exists in the simulation data
    known = set(results.scores.keys())
    for name in team_a_names + team_b_names:
        if name not in known:
            raise ValueError(f"Player not found in simulation results: {name!r}")

    n = results.n_simulations

    # Build per-simulation totals by summing each roster's scores trial-by-trial
    # zip(*list_of_lists) transposes: we get one tuple of scores per simulation
    team_a_totals = [
        sum(scores[i] for scores in (results.scores[name] for name in team_a_names))
        for i in range(n)
    ]
    team_b_totals = [
        sum(scores[i] for scores in (results.scores[name] for name in team_b_names))
        for i in range(n)
    ]

    # Tally outcomes across all simulations
    a_wins = sum(1 for a, b in zip(team_a_totals, team_b_totals) if a > b)
    b_wins = sum(1 for a, b in zip(team_a_totals, team_b_totals) if b > a)
    ties   = n - a_wins - b_wins

    margins = [a - b for a, b in zip(team_a_totals, team_b_totals)]

    return H2HResult(
        team_a_win_pct=100 * a_wins / n,
        team_b_win_pct=100 * b_wins / n,
        tie_pct=100 * ties / n,
        avg_margin=statistics.mean(margins),
        team_a_mean=statistics.mean(team_a_totals),
        team_b_mean=statistics.mean(team_b_totals),
    )


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
