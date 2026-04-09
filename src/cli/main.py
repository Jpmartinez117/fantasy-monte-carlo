"""Entry point for the Fantasy Draft helper CLI.

Usage:
    python -m src.cli.main                  # uses data/players.csv, 10,000 sims
    python -m src.cli.main path/to/file.csv # custom data file
    python -m src.cli.main file.csv 50000   # custom file + simulation count
"""

import sys

from src.data_loader.base import DataLoadError
from src.data_loader.csv_loader import CsvPlayerProvider
from src.simulation.monte_carlo import run_simulation
from src.stats.statistics_engine import PlayerStats, compute_stats, rank_players

DEFAULT_CSV = "data/players.csv"
DEFAULT_SIMS = 10_000


def main() -> None:
    # --- Parse CLI arguments (minimal, no third-party deps) ---
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    try:
        n_sims = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_SIMS
        if n_sims < 1:
            raise ValueError
    except ValueError:
        print(f"[ERROR] simulation count must be a positive integer, got {sys.argv[2]!r}")
        sys.exit(1)

    # --- Load players from CSV ---
    print(f"Loading players from {csv_path!r}...")
    try:
        players = CsvPlayerProvider(csv_path).load_players()
    except DataLoadError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    if not players:
        print("[ERROR] No valid players were loaded. Exiting.")
        sys.exit(1)

    print(f"Loaded {len(players)} players.\n")

    # --- Run Monte Carlo simulation ---
    print(f"Running {n_sims:,} simulations...")
    results = run_simulation(players, n_simulations=n_sims)

    # --- Compute per-player stats and rank ---
    stats = compute_stats(results, players)
    ranked = rank_players(stats)

    # --- Print results table ---
    _print_table(ranked)


def _print_table(ranked: list) -> None:
    """Print a formatted leaderboard of player simulation results."""
    # Column header matches the order of data printed below
    col_header = (
        f"{'Rank':<5} {'Name':<22} {'Pos':<5} "
        f"{'Mean':>6} {'StdDev':>7} "
        f"{'P10':>6} {'P25':>6} {'P50':>6} {'P75':>6} {'P90':>6}"
    )
    divider = "-" * len(col_header)

    print(f"\n{col_header}")
    print(divider)

    for rank, s in enumerate(ranked, start=1):
        print(
            f"{rank:<5} {s.name:<22} {s.position:<5} "
            f"{s.mean:>6.2f} {s.std_dev:>7.2f} "
            f"{s.p10:>6.2f} {s.p25:>6.2f} {s.median:>6.2f} {s.p75:>6.2f} {s.p90:>6.2f}"
        )


if __name__ == "__main__":
    main()
