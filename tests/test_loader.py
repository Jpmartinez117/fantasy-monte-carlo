"""Unit tests for the CSV data loader."""

from pathlib import Path

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


# ---------------------------------------------------------------------------
# File-level encoding edge cases (bug fixes #1, #2, #7)
# ---------------------------------------------------------------------------

class TestFileEncoding:
    def test_utf8_bom_at_start_of_file_is_handled(self, tmp_path: Path):
        """Files saved by Excel / Notepad++ often begin with a UTF-8 BOM.
        The loader must strip it transparently, not reject the header."""
        p = tmp_path / "with_bom.csv"
        # ﻿ is the BOM; encoding it as UTF-8 produces the EF BB BF byte sequence.
        content = "﻿Name,Position,Mean,StdDev\nJosh Harper,QB,24.5,4.8\n"
        p.write_bytes(content.encode("utf-8"))

        players = CsvPlayerProvider(p).load_players()
        assert len(players) == 1
        assert players[0].name == "Josh Harper"

    def test_non_utf8_file_raises_friendly_error(self, tmp_path: Path):
        """A file with non-UTF-8 bytes should produce a DataLoadError with a
        clear message instead of a UnicodeDecodeError traceback."""
        p = tmp_path / "cp1252.csv"
        # \xe9 is é in cp1252 / latin-1 but is an invalid lone start byte in UTF-8.
        p.write_bytes(b"Name,Position,Mean,StdDev\nJos\xe9 Harper,QB,24.5,4.8\n")

        with pytest.raises(DataLoadError, match="UTF-8"):
            CsvPlayerProvider(p).load_players()


class TestEmbeddedNewlines:
    def test_quoted_field_with_embedded_newline_parses_as_one_row(self):
        """A quoted field containing a newline should be treated as a single
        cell — not split across two rows that each fail column-count validation.
        (Bug #7: previously csv.reader was fed pre-split lines via splitlines().)"""
        # Quoted name spans two physical lines but is logically one field.
        text = (
            'Name,Position,Mean,StdDev\n'
            '"Smith\nJr.",QB,24.5,4.8\n'
        )
        players, warnings = _parse_csv(text)

        # The row parses as exactly one player with no column-count warnings.
        assert len(players) == 1
        assert "Smith" in players[0].name
        assert not any("column count" in w for w in warnings)
