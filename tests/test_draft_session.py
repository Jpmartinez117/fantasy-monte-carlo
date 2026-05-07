"""Unit tests for draft session input resolution.

These exercise `_resolve_pick` directly so we don't have to drive the
interactive REPL via subprocess.  The function is the only piece of
draft_session that contains real logic; the rest is I/O.
"""

import pytest

from src.cli.draft_session import _resolve_pick
from src.stats.statistics_engine import PlayerStats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _stat(name: str, position: str = "QB", mean: float = 20.0) -> PlayerStats:
    """Build a PlayerStats with placeholder distribution fields."""
    return PlayerStats(
        name=name, position=position, mean=mean, std_dev=4.0,
        median=mean, p10=mean - 5, p25=mean - 2, p75=mean + 2, p90=mean + 5,
    )


@pytest.fixture
def board() -> list[PlayerStats]:
    # Order matters — _resolve_pick treats this list as ranked
    return [
        _stat("Patrick Keller", "QB", 25.0),
        _stat("Josh Harper", "QB", 24.0),
        _stat("Jalen Fields", "QB", 22.0),
        _stat("Derrick Miles", "RB", 18.0),
    ]


# ---------------------------------------------------------------------------
# Numeric rank input
# ---------------------------------------------------------------------------

class TestNumericPick:
    def test_rank_1_returns_first_player(self, board):
        assert _resolve_pick("1", board).name == "Patrick Keller"

    def test_rank_within_range_returns_correct_player(self, board):
        assert _resolve_pick("3", board).name == "Jalen Fields"

    def test_rank_zero_returns_none(self, board):
        # Rank is 1-based; "0" maps to index -1 which is out of bounds for our check
        assert _resolve_pick("0", board) is None

    def test_rank_above_range_returns_none(self, board):
        assert _resolve_pick("99", board) is None


# ---------------------------------------------------------------------------
# Name substring input
# ---------------------------------------------------------------------------

class TestNamePick:
    def test_unique_substring_returns_player(self, board):
        # "harp" should match only Josh Harper
        assert _resolve_pick("harp", board).name == "Josh Harper"

    def test_match_is_case_insensitive(self, board):
        assert _resolve_pick("KELLER", board).name == "Patrick Keller"

    def test_no_match_returns_none(self, board):
        assert _resolve_pick("Nonexistent", board) is None

    def test_ambiguous_substring_returns_none(self, board, capsys):
        # "QB" appears in three names via the position string?  No — only via
        # actual name content.  Use a substring that hits multiple players.
        # All three QB players contain a space + capital letter; pick "a"
        # which is in Patrick, Harper, Jalen.
        result = _resolve_pick("a", board)
        assert result is None
        # Ambiguity is reported to stdout for the user
        captured = capsys.readouterr()
        assert "Ambiguous" in captured.out
