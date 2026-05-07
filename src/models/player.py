"""Player model — core data structure for a fantasy football player."""

from dataclasses import dataclass


VALID_POSITIONS = {"QB", "RB", "WR", "TE"}

# Single source of truth for the legal numeric ranges of a Player's stats.
# Both the model's __post_init__ and the CSV loader's row validation import
# from here so a tuning change to one rule cannot drift the other.
MIN_MEAN = 0
MAX_MEAN = 60
MIN_STD_DEV = 0
MAX_STD_DEV = 25


@dataclass(frozen=True)
class Player:
    """Represents a single fantasy football player with projected stats.

    Attributes:
        name:     Player's full name.
        position: Fantasy position (QB, RB, WR, or TE).
        mean:     Expected weekly fantasy points.
        std_dev:  Weekly volatility (standard deviation of fantasy points).
    """

    name: str
    position: str
    mean: float
    std_dev: float

    def __post_init__(self):
        # Reject both an empty string and a whitespace-only string.  The CSV
        # loader already strips before constructing Player, but this guard
        # protects any direct caller (tests, future code paths) from creating
        # a "blank-named" player that the rest of the system would mis-handle.
        if not self.name.strip():
            raise ValueError("Player name cannot be empty")
        if self.position not in VALID_POSITIONS:
            raise ValueError(
                f"Invalid position {self.position!r}. Must be one of {sorted(VALID_POSITIONS)}"
            )
        if not (MIN_MEAN <= self.mean <= MAX_MEAN):
            raise ValueError(
                f"Mean must be between {MIN_MEAN} and {MAX_MEAN}, got {self.mean}"
            )
        if not (MIN_STD_DEV <= self.std_dev <= MAX_STD_DEV):
            raise ValueError(
                f"StdDev must be between {MIN_STD_DEV} and {MAX_STD_DEV}, got {self.std_dev}"
            )

    def __str__(self):
        return f"{self.name} ({self.position}) — mean={self.mean}, std_dev={self.std_dev}"
