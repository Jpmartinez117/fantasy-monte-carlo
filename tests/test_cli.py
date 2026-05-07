"""End-to-end CLI smoke tests.

These tests invoke `python -m src.cli.main` as a subprocess against a
small temporary CSV fixture.  They are intentionally smoke-only: each
test checks exit code and a few load-bearing strings in stdout, not
exact formatting.  Lower-level math correctness is already covered by
the simulation/stats unit tests.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Small roster — keeps simulations fast and gives us deterministic player
# names for filter / h2h / missing-name assertions.
_FIXTURE_CSV = (
    "Name,Position,Mean,StdDev\n"
    "Alpha QB,QB,25.0,5.0\n"
    "Bravo QB,QB,22.0,4.5\n"
    "Charlie RB,RB,18.0,4.0\n"
    "Delta WR,WR,15.0,3.5\n"
    "Echo TE,TE,12.0,3.0\n"
)


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    """Write the fixture CSV to a tmp directory and return its path."""
    p = tmp_path / "players.csv"
    p.write_text(_FIXTURE_CSV, encoding="utf-8")
    return p


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI as a subprocess and return the completed process.

    Uses --sims 100 by default in callers to keep each test fast.
    text=True + utf-8 encoding avoids Windows cp1252 fallback on em-dash chars.
    """
    return subprocess.run(
        [sys.executable, "-m", "src.cli.main", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# 3a — Default rankings mode
# ---------------------------------------------------------------------------

class TestDefaultRankings:
    def test_exits_successfully(self, csv_path: Path):
        result = run_cli("--file", str(csv_path), "--sims", "100")
        assert result.returncode == 0, result.stderr

    def test_reports_player_count(self, csv_path: Path):
        result = run_cli("--file", str(csv_path), "--sims", "100")
        assert "Loaded 5 players" in result.stdout

    def test_prints_table_header_and_all_players(self, csv_path: Path):
        result = run_cli("--file", str(csv_path), "--sims", "100")
        # Table header columns
        assert "Rank" in result.stdout
        assert "Mean" in result.stdout
        assert "P90" in result.stdout
        # Every fixture player appears in the output
        for name in ("Alpha QB", "Bravo QB", "Charlie RB", "Delta WR", "Echo TE"):
            assert name in result.stdout

    def test_top_player_is_alpha(self, csv_path: Path):
        # Alpha QB has the highest mean (25.0); should be ranked #1
        result = run_cli("--file", str(csv_path), "--sims", "100")
        # Find the line that starts with "1 " (rank 1) and check the name
        rank1_line = next(
            line for line in result.stdout.splitlines() if line.startswith("1 ")
        )
        assert "Alpha QB" in rank1_line


# ---------------------------------------------------------------------------
# 3b — Position filter and top slice
# ---------------------------------------------------------------------------

class TestFilterAndSlice:
    def test_pos_filter_includes_only_qbs(self, csv_path: Path):
        result = run_cli("--file", str(csv_path), "--sims", "100", "--pos", "QB")
        assert result.returncode == 0
        # Both QBs present
        assert "Alpha QB" in result.stdout
        assert "Bravo QB" in result.stdout
        # Non-QBs absent
        assert "Charlie RB" not in result.stdout
        assert "Delta WR" not in result.stdout
        assert "Echo TE" not in result.stdout

    def test_top_slice_limits_rows(self, csv_path: Path):
        result = run_cli("--file", str(csv_path), "--sims", "100", "--top", "2")
        assert result.returncode == 0
        # Top two by mean are Alpha QB (25) and Bravo QB (22)
        assert "Alpha QB" in result.stdout
        assert "Bravo QB" in result.stdout
        # Lower-ranked players should be sliced out
        assert "Charlie RB" not in result.stdout
        assert "Echo TE" not in result.stdout

    def test_pos_with_top_combined(self, csv_path: Path):
        # Filter to QBs then take top 1 — should leave only Alpha QB
        result = run_cli(
            "--file", str(csv_path), "--sims", "100", "--pos", "QB", "--top", "1"
        )
        assert result.returncode == 0
        assert "Alpha QB" in result.stdout
        assert "Bravo QB" not in result.stdout

    def test_pos_filter_with_no_matches_warns(self, csv_path: Path):
        # The fixture has no players outside QB/RB/WR/TE — but if we filter to
        # a position with no candidates after some hypothetical slice, the CLI
        # should still exit 0 and surface a warning.  We force this by combining
        # a position filter with an empty result set: pick an extreme top value
        # of 0 won't work (CLI rejects --top 0).  Instead, write a roster with
        # no QBs and filter to QB.
        no_qb_csv = csv_path.parent / "no_qbs.csv"
        no_qb_csv.write_text(
            "Name,Position,Mean,StdDev\n"
            "Solo RB,RB,18.0,4.0\n",
            encoding="utf-8",
        )
        result = run_cli("--file", str(no_qb_csv), "--sims", "100", "--pos", "QB")
        assert result.returncode == 0
        assert "WARNING" in result.stdout
        assert "QB" in result.stdout


# ---------------------------------------------------------------------------
# 3c — Head-to-head mode
# ---------------------------------------------------------------------------

class TestHeadToHead:
    def test_h2h_prints_summary(self, csv_path: Path):
        result = run_cli(
            "--file", str(csv_path),
            "--sims", "200",
            "--h2h", "Alpha QB,Charlie RB", "Bravo QB,Delta WR",
        )
        assert result.returncode == 0, result.stderr
        # Section header and the key stat lines should all be present
        assert "Head-to-Head Results" in result.stdout
        assert "Team A win %" in result.stdout
        assert "Team B win %" in result.stdout
        assert "Avg margin" in result.stdout

    def test_h2h_unknown_player_fails(self, csv_path: Path):
        # Misspelled name — should trigger the validation error and exit 1
        result = run_cli(
            "--file", str(csv_path),
            "--sims", "100",
            "--h2h", "Alpha QB,Nobody", "Bravo QB,Delta WR",
        )
        assert result.returncode == 1
        assert "Player not found" in result.stdout or "Player not found" in result.stderr


# ---------------------------------------------------------------------------
# 3d — Failure paths (missing file, invalid args)
# ---------------------------------------------------------------------------

class TestFailurePaths:
    def test_missing_file_exits_with_error(self, tmp_path: Path):
        # Path that definitely does not exist
        bogus = tmp_path / "does_not_exist.csv"
        result = run_cli("--file", str(bogus), "--sims", "100")
        assert result.returncode == 1
        # Error should mention the file is missing
        assert "ERROR" in result.stdout
        assert "not found" in result.stdout

    def test_zero_sims_rejected_by_argparse(self, csv_path: Path):
        # argparse-level validation; exits with code 2 (argparse convention)
        result = run_cli("--file", str(csv_path), "--sims", "0")
        assert result.returncode == 2
        # argparse writes the error to stderr
        assert "--sims" in result.stderr

    def test_h2h_and_draft_mutually_exclusive(self, csv_path: Path):
        # argparse validation: mutually exclusive flag combo
        result = run_cli(
            "--file", str(csv_path),
            "--draft",
            "--h2h", "Alpha QB", "Bravo QB",
        )
        assert result.returncode == 2
        assert "h2h" in result.stderr.lower() or "draft" in result.stderr.lower()
