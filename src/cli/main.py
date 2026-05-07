"""Entry point for the Fantasy Draft helper CLI.

Usage examples:
    python -m src.cli.main
    python -m src.cli.main --file data/players.csv --sims 50000
    python -m src.cli.main --pos QB --top 5
    python -m src.cli.main --draft
    python -m src.cli.main --h2h "Josh Harper,Derrick Miles" "Patrick Keller,Christian Grant"
"""

import argparse
import sys

from src.data_loader.base import DataLoadError
from src.data_loader.csv_loader import CsvPlayerProvider
from src.models.player import VALID_POSITIONS
from src.simulation.monte_carlo import run_simulation
from src.stats.statistics_engine import PlayerStats, compute_stats, head_to_head, rank_players

DEFAULT_CSV = "data/players.csv"
DEFAULT_SIMS = 10_000

# Hard upper bounds to turn cryptic resource-exhaustion crashes into friendly
# argparse / CLI errors.  Both ceilings sit well past any realistic use:
# 10M simulations is several minutes of pure-Python work, and 50 players is
# already 4-5x a normal fantasy roster.
MAX_SIMS = 10_000_000
MAX_ROSTER_SIZE = 50


def main() -> None:
    args = _parse_args()

    # --- Load players ---
    print(f"Loading players from {args.file!r}...")
    try:
        players = CsvPlayerProvider(args.file).load_players()
    except DataLoadError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    if not players:
        print("[ERROR] No valid players were loaded. Exiting.")
        sys.exit(1)

    print(f"Loaded {len(players)} players.\n")

    # --- Run simulation once — all downstream modes share these results ---
    print(f"Running {args.sims:,} simulations...")
    results = run_simulation(players, n_simulations=args.sims)

    stats = compute_stats(results, players)
    ranked = rank_players(stats)

    # --- Dispatch to the requested mode ---
    if args.h2h:
        _run_h2h(args.h2h, results, players)
    elif args.draft:
        # Import here to keep the draft session isolated from the standard flow
        from src.cli.draft_session import run_draft_session
        run_draft_session(ranked)
    else:
        _run_rankings(ranked, pos_filter=args.pos, top=args.top)


# ---------------------------------------------------------------------------
# Rankings mode (default)
# ---------------------------------------------------------------------------

def _run_rankings(
    ranked: list,
    pos_filter: str | None = None,
    top: int | None = None,
) -> None:
    """Filter, slice, and print the rankings table."""
    # Apply position filter if requested
    if pos_filter:
        ranked = [s for s in ranked if s.position == pos_filter]
        if not ranked:
            print(f"[WARNING] No players found for position {pos_filter!r}")
            return

    # Limit to top-N rows if requested
    if top:
        ranked = ranked[:top]

    print_table(ranked)


# ---------------------------------------------------------------------------
# Head-to-head mode
# ---------------------------------------------------------------------------

def _run_h2h(h2h_args: list[str], results, players) -> None:
    """Parse the two roster strings and print a head-to-head matchup report."""
    team_a_names = [n.strip() for n in h2h_args[0].split(",")]
    team_b_names = [n.strip() for n in h2h_args[1].split(",")]

    # Reject obviously oversized rosters early.  A real fantasy roster is
    # 8-12 starters; anything past MAX_ROSTER_SIZE is almost certainly a
    # paste error (e.g. an entire ranking copied into one --h2h argument)
    # and would otherwise just waste simulation work.
    for label, names in (("Team A", team_a_names), ("Team B", team_b_names)):
        if len(names) > MAX_ROSTER_SIZE:
            print(
                f"[ERROR] {label} has {len(names)} players "
                f"(maximum allowed is {MAX_ROSTER_SIZE})"
            )
            sys.exit(1)

    # Validate that every name appears in the simulation results
    known = set(results.scores.keys())
    for name in team_a_names + team_b_names:
        if name not in known:
            print(f"[ERROR] Player not found in simulation: {name!r}")
            sys.exit(1)

    h2h = head_to_head(results, team_a_names, team_b_names)

    print("\n--- Head-to-Head Results ---")
    print(f"Team A: {', '.join(team_a_names)}")
    print(f"Team B: {', '.join(team_b_names)}")
    print(f"\n  Team A win %  : {h2h.team_a_win_pct:.1f}%")
    print(f"  Team B win %  : {h2h.team_b_win_pct:.1f}%")
    print(f"  Tie %         : {h2h.tie_pct:.1f}%")
    print(f"  Avg margin    : {h2h.avg_margin:+.2f} pts (positive = Team A advantage)")
    print(f"  Team A avg    : {h2h.team_a_mean:.2f} pts/week")
    print(f"  Team B avg    : {h2h.team_b_mean:.2f} pts/week")


# ---------------------------------------------------------------------------
# Shared table printer (used by rankings mode and draft session)
# ---------------------------------------------------------------------------

def print_table(ranked: list, show_rank: bool = True) -> None:
    """Print a formatted leaderboard table.

    Args:
        ranked:    Ordered list of PlayerStats to display.
        show_rank: Whether to include the Rank column (False in draft session).
    """
    # Optional Rank prefix — width matches the rank-number prefix below so
    # the header and rows stay aligned regardless of the show_rank flag.
    header_rank = f"{'Rank':<5} " if show_rank else ""
    body_columns = (
        f"{'Name':<22} {'Pos':<5} "
        f"{'Mean':>6} {'StdDev':>7} "
        f"{'P10':>6} {'P25':>6} {'P50':>6} {'P75':>6} {'P90':>6}"
    )
    header = f"{header_rank}{body_columns}"

    print(f"\n{header}")
    print("-" * len(header))

    for rank, s in enumerate(ranked, start=1):
        row_rank = f"{rank:<5} " if show_rank else ""
        print(
            f"{row_rank}{s.name:<22} {s.position:<5} "
            f"{s.mean:>6.2f} {s.std_dev:>7.2f} "
            f"{s.p10:>6.2f} {s.p25:>6.2f} {s.median:>6.2f} {s.p75:>6.2f} {s.p90:>6.2f}"
        )


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fantasy-mc",
        description="Fantasy Football Monte Carlo Draft Helper",
    )
    parser.add_argument(
        "--file", "-f",
        default=DEFAULT_CSV,
        metavar="PATH",
        help=f"CSV player file (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--sims", "-s",
        type=int,
        default=DEFAULT_SIMS,
        metavar="N",
        help=f"Number of Monte Carlo simulations (default: {DEFAULT_SIMS:,})",
    )
    parser.add_argument(
        "--pos", "-p",
        choices=sorted(VALID_POSITIONS),
        metavar="POS",
        help="Filter rankings to a single position: QB, RB, TE, WR",
    )
    parser.add_argument(
        "--top", "-t",
        type=int,
        metavar="N",
        help="Show only the top N players",
    )
    parser.add_argument(
        "--draft", "-d",
        action="store_true",
        help="Launch interactive draft session",
    )
    parser.add_argument(
        "--h2h",
        nargs=2,
        metavar=("TEAM_A", "TEAM_B"),
        help=(
            'Head-to-head comparison. Pass two quoted comma-separated player lists. '
            'Example: --h2h "Josh Harper,Derrick Miles" "Patrick Keller,Christian Grant"'
        ),
    )

    args = parser.parse_args()

    # Validate sims is positive and below the safety ceiling.  The upper
    # bound prevents a typo like `--sims 999999999` from triggering a
    # MemoryError partway through allocation.
    if args.sims < 1:
        parser.error(f"--sims must be >= 1, got {args.sims}")
    if args.sims > MAX_SIMS:
        parser.error(f"--sims must be <= {MAX_SIMS:,}, got {args.sims:,}")

    # Validate --top is positive if provided
    if args.top is not None and args.top < 1:
        parser.error(f"--top must be >= 1, got {args.top}")

    # --h2h and --draft are mutually exclusive
    if args.h2h and args.draft:
        parser.error("--h2h and --draft cannot be used together")

    return args


if __name__ == "__main__":
    main()
