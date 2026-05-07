"""Unit tests for the Player dataclass validation rules.

The CSV loader path is heavily covered by tests/test_loader.py. These
tests exercise direct Player construction — the public surface any
caller (tests, future modules) would use to build Player objects
without going through a CSV.
"""

import pytest

from src.models.player import Player


class TestPlayerValidation:
    def test_valid_player_constructs(self):
        p = Player(name="Josh Harper", position="QB", mean=24.5, std_dev=4.8)
        assert p.name == "Josh Harper"

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            Player(name="", position="QB", mean=20.0, std_dev=4.0)

    # --- Bug fix #8 --------------------------------------------------------

    def test_whitespace_only_name_rejected(self):
        # Previously slipped through `if not self.name` because a non-empty
        # whitespace string is truthy.  Should now be rejected on the same
        # path as an empty string.
        with pytest.raises(ValueError, match="empty"):
            Player(name="   ", position="QB", mean=20.0, std_dev=4.0)

    def test_tab_only_name_rejected(self):
        with pytest.raises(ValueError, match="empty"):
            Player(name="\t\t", position="QB", mean=20.0, std_dev=4.0)

    # --- Other guard rails (not part of this fix, but worth pinning) -------

    def test_invalid_position_rejected(self):
        with pytest.raises(ValueError, match="position"):
            Player(name="X", position="K", mean=20.0, std_dev=4.0)

    def test_mean_out_of_range_rejected(self):
        with pytest.raises(ValueError, match="Mean"):
            Player(name="X", position="QB", mean=999.0, std_dev=4.0)

    def test_stddev_out_of_range_rejected(self):
        with pytest.raises(ValueError, match="StdDev"):
            Player(name="X", position="QB", mean=20.0, std_dev=999.0)
