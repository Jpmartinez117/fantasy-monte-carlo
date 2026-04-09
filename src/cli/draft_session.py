"""Interactive draft session — pick players off the board in real time."""

from typing import List

from src.stats.statistics_engine import PlayerStats


def run_draft_session(ranked: List[PlayerStats]) -> None:
    """Run a REPL-style draft session.

    Displays the full ranked board, then waits for the user to enter a rank
    number or player name to mark as drafted.  After each pick the board
    refreshes showing only undrafted players.  A position summary is printed
    after each pick so the user can track remaining positional depth.

    Commands:
        <number>  — draft the player at that rank
        q / quit  — exit the session
    """
    # Work from a mutable copy so we don't modify the caller's list
    available: List[PlayerStats] = list(ranked)
    drafted: List[PlayerStats] = []

    print("\n=== DRAFT SESSION STARTED ===")
    print("Commands: enter a rank number to draft a player, or 'q' to quit.\n")

    while available:
        _display_board(available)
        _display_position_summary(available)

        pick = input("\nYour pick > ").strip()

        if pick.lower() in ("q", "quit", "exit"):
            print("\nDraft session ended.")
            break

        # Try to resolve the input as a rank number first, then as a name substring
        player = _resolve_pick(pick, available)
        if player is None:
            print(f"  [!] Could not find {pick!r} — try a rank number or part of a name.")
            continue

        available.remove(player)
        drafted.append(player)
        pick_num = len(drafted)
        print(f"\n  >>> Pick #{pick_num}: {player.name} ({player.position}) drafted!")

    # Show final draft recap when the session ends
    if drafted:
        _display_recap(drafted)


def _resolve_pick(pick: str, available: List[PlayerStats]) -> PlayerStats | None:
    """Return the PlayerStats that matches the user's input, or None.

    Tries rank number first (1-based), then case-insensitive name substring.
    """
    # Attempt numeric rank
    if pick.isdigit():
        idx = int(pick) - 1  # convert 1-based rank to 0-based index
        if 0 <= idx < len(available):
            return available[idx]
        return None  # rank is out of range

    # Fall back to name substring match (case-insensitive)
    needle = pick.lower()
    matches = [p for p in available if needle in p.name.lower()]

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # Ambiguous — show options so the user can be more specific
        print(f"  [!] Ambiguous — {len(matches)} players match {pick!r}:")
        for m in matches:
            print(f"      {m.name} ({m.position})")
    return None


def _display_board(available: List[PlayerStats]) -> None:
    """Print the current available-player board with rank numbers."""
    from src.cli.main import print_table  # local import avoids circular dependency at module load

    print(f"\n{'='*70}")
    print(f"  AVAILABLE PLAYERS  ({len(available)} remaining)")
    print(f"{'='*70}")
    print_table(available, show_rank=True)


def _display_position_summary(available: List[PlayerStats]) -> None:
    """Print a quick count of remaining players per position."""
    from src.models.player import VALID_POSITIONS

    counts = {pos: 0 for pos in sorted(VALID_POSITIONS)}
    for p in available:
        counts[p.position] = counts.get(p.position, 0) + 1

    parts = [f"{pos}: {counts[pos]}" for pos in sorted(counts)]
    print("\n  Remaining depth — " + "  |  ".join(parts))


def _display_recap(drafted: List[PlayerStats]) -> None:
    """Print a summary of all players drafted this session."""
    from src.cli.main import print_table

    print(f"\n{'='*70}")
    print(f"  DRAFT RECAP  ({len(drafted)} picks)")
    print(f"{'='*70}")

    # Show in draft order (not re-ranked) so the user sees their pick sequence
    print_table(drafted, show_rank=False)
