"""Unit tests for the CSV data loader."""

import pytest
from src.data_loader.base import DataLoadError
from src.data_loader.csv_loader import CsvPlayerProvider, _parse_csv


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse(text: str):
    """Shorthand: parse raw CSV text and return (players, warnings)."""
    return _parse_csv(text)


# ---------------------------------------------------------------------------
# Header validation
# ---------------------------------------------------------------------------

class TestHeader:
    def test_empty_file_raises(self):
        with pytest.raises(DataLoadError, match="empty"):
            parse("")

    def test_wrong_header_raises(self):
        with pytest.raises(DataLoadError, match="Bad header"):
            parse("name,pos,avg,sd\nJosh Harper,QB,24.5,4.8")

    def test_extra_column_in_header_raises(self):
        with pytest.raises(DataLoadError, match="Bad header"):
            parse("Name,Position,Mean,StdDev,Team\nJosh Harper,QB,24.5,4.8,DAL")

    def test_correct_header_accepted(self):
        players, warnings = parse("Name,Position,Mean,StdDev\nJosh Harper,QB,24.5,4.8")
        assert len(players) == 1
        assert not warnings


# ---------------------------------------------------------------------------
# Valid rows
# ---------------------------------------------------------------------------

class TestValidRows:
    def test_single_valid_row(self):
        players, warnings = parse("Name,Position,Mean,StdDev\nJosh Harper,QB,24.5,4.8")
        assert len(players) == 1
        p = players[0]
        assert p.name == "Josh Harper"
        assert p.position == "QB"
        assert p.mean == 24.5
        assert p.std_dev == 4.8

    def test_all_four_positions_accepted(self):
        csv = (
            "Name,Position,Mean,StdDev\n"
            "A,QB,20.0,4.0\n"
            "B,RB,15.0,3.0\n"
            "C,WR,14.0,3.0\n"
            "D,TE,10.0,2.0\n"
        )
        players, warnings = parse(csv)
        assert len(players) == 4
        assert not warnings

    def test_position_lowercase_normalised(self):
        # Loader should uppercase position before validation
        players, _ = parse("Name,Position,Mean,StdDev\nAlex,qb,20.0,4.0")
        assert players[0].position == "QB"

    def test_whitespace_trimmed_from_name(self):
        players, _ = parse("Name,Position,Mean,StdDev\n  Josh Harper  ,QB,24.5,4.8")
        assert players[0].name == "Josh Harper"

    def test_boundary_values_accepted(self):
        # Mean=0, StdDev=0 and Mean=60, StdDev=25 should both be valid
        csv = (
            "Name,Position,Mean,StdDev\n"
            "Low,QB,0,0\n"
            "High,QB,60,25\n"
        )
        players, warnings = parse(csv)
        assert len(players) == 2
        assert not warnings

    def test_blank_lines_skipped(self):
        csv = "Name,Position,Mean,StdDev\n\nJosh Harper,QB,24.5,4.8\n\n"
        players, warnings = parse(csv)
        assert len(players) == 1
        assert not warnings


# ---------------------------------------------------------------------------
# Invalid rows — each should produce a warning and be skipped
# ---------------------------------------------------------------------------

class TestInvalidRows:
    def test_non_numeric_mean_skipped(self):
        csv = "Name,Position,Mean,StdDev\nBobby Thrower,QB,twelve,4.1"
        players, warnings = parse(csv)
        assert players == []
        assert any("non-numeric" in w for w in warnings)

    def test_empty_stddev_skipped(self):
        csv = "Name,Position,Mean,StdDev\nAlex Runner,RB,14.5,"
        players, warnings = parse(csv)
        assert players == []

    def test_negative_stddev_skipped(self):
        csv = "Name,Position,Mean,StdDev\nCharlie Power,RB,11.8,-2.0"
        players, warnings = parse(csv)
        assert players == []
        assert any("StdDev" in w for w in warnings)

    def test_invalid_position_skipped(self):
        csv = "Name,Position,Mean,StdDev\nDerek Kicker,K,8.0,1.5"
        players, warnings = parse(csv)
        assert players == []
        assert any("K" in w for w in warnings)

    def test_empty_name_skipped(self):
        csv = "Name,Position,Mean,StdDev\n,WR,13.2,3.1"
        players, warnings = parse(csv)
        assert players == []

    def test_negative_mean_skipped(self):
        csv = "Name,Position,Mean,StdDev\nEvan Holder,TE,-3.0,2.1"
        players, warnings = parse(csv)
        assert players == []
        assert any("Mean" in w for w in warnings)

    def test_stddev_above_max_skipped(self):
        csv = "Name,Position,Mean,StdDev\nFrank Catch,WR,10.5,50.0"
        players, warnings = parse(csv)
        assert players == []
        assert any("StdDev" in w for w in warnings)

    def test_extra_column_row_skipped(self):
        # "Smith, John" will split into 5 fields due to the embedded comma
        csv = "Name,Position,Mean,StdDev\nSmith, John,WR,12.0,2.8"
        players, warnings = parse(csv)
        assert players == []
        assert any("column count" in w for w in warnings)

    def test_missing_position_skipped(self):
        csv = "Name,Position,Mean,StdDev\nHank Unknown,,9.0,2.0"
        players, warnings = parse(csv)
        assert players == []

    def test_extra_trailing_column_skipped(self):
        csv = "Name,Position,Mean,StdDev\nIke Extra,QB,18.0,3.0,DAL"
        players, warnings = parse(csv)
        assert players == []
        assert any("column count" in w for w in warnings)


# ---------------------------------------------------------------------------
# Duplicate handling
# ---------------------------------------------------------------------------

class TestDuplicates:
    def test_first_occurrence_kept(self):
        csv = (
            "Name,Position,Mean,StdDev\n"
            "Gabe Repeat,QB,19.0,4.0\n"
            "Gabe Repeat,QB,19.0,4.0\n"
        )
        players, warnings = parse(csv)
        assert len(players) == 1
        assert any("Duplicate" in w for w in warnings)

    def test_same_name_different_position_allowed(self):
        # Two players with the same name but different positions are distinct
        csv = (
            "Name,Position,Mean,StdDev\n"
            "Chris Multi,QB,20.0,4.0\n"
            "Chris Multi,RB,14.0,3.0\n"
        )
        players, warnings = parse(csv)
        assert len(players) == 2
        assert not warnings


# ---------------------------------------------------------------------------
# Full bad file integration test
# ---------------------------------------------------------------------------

class TestBadFile:
    def test_bad_csv_file(self):
        """Run the loader against players_bad.csv; only Gabe Repeat should load."""
        provider = CsvPlayerProvider("data/players_bad.csv")
        players = provider.load_players()  # warnings printed to stdout, not raised
        # Only "Gabe Repeat" first occurrence survives all validation rules
        assert len(players) == 1
        assert players[0].name == "Gabe Repeat"
        assert players[0].position == "QB"

    def test_missing_file_raises(self):
        with pytest.raises(DataLoadError, match="not found"):
            CsvPlayerProvider("data/no_such_file.csv").load_players()
