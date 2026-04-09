"""Monte Carlo simulation engine for fantasy football scoring."""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.models.player import Player


@dataclass
class SimulationResults:
    """Holds raw per-player simulated scores from a single Monte Carlo run.

    Attributes:
        scores:        Maps each player's name to a list of N simulated scores.
        n_simulations: Number of simulations that were run.
    """
    scores: Dict[str, List[float]] = field(default_factory=dict)
    n_simulations: int = 0


def run_simulation(
    players: List[Player],
    n_simulations: int = 10_000,
    seed: Optional[int] = None,
) -> SimulationResults:
    """Run Monte Carlo simulation for a list of players.

    For each of the N simulations, each player draws a weekly fantasy score
    from a normal distribution N(mean, std_dev).  Scores are clamped to 0
    because a player can never score negative points.

    Args:
        players:       Players to simulate (must be non-empty).
        n_simulations: Number of independent trials (default 10,000).
        seed:          Optional integer seed for reproducibility.

    Returns:
        SimulationResults with a list of N scores per player.

    Raises:
        ValueError: If players is empty or n_simulations < 1.
    """
    if not players:
        raise ValueError("Player list cannot be empty")
    if n_simulations < 1:
        raise ValueError(f"n_simulations must be >= 1, got {n_simulations}")

    # Use an isolated Random instance so we don't affect Python's global RNG
    rng = random.Random(seed)

    # Pre-allocate one list per player to avoid repeated dict look-ups inside the loop
    scores: Dict[str, List[float]] = {p.name: [] for p in players}

    # --- Core Monte Carlo loop ---
    # Each iteration is one "week" — every player gets an independent score draw
    for _ in range(n_simulations):
        for player in players:
            # Sample from the player's distribution; clamp negatives to 0
            raw = rng.gauss(player.mean, player.std_dev)
            scores[player.name].append(max(0.0, raw))

    return SimulationResults(scores=scores, n_simulations=n_simulations)
