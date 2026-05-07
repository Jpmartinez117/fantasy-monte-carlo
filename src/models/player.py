"""Player model — core data structure for a fantasy football player."""

from dataclasses import dataclass


VALID_POSITIONS = {"QB", "RB", "WR", "TE"}


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
        if not (0 <= self.mean <= 60):
            raise ValueError(f"Mean must be between 0 and 60, got {self.mean}")
        if not (0 <= self.std_dev <= 25):
            raise ValueError(f"StdDev must be between 0 and 25, got {self.std_dev}")

    def __str__(self):
        return f"{self.name} ({self.position}) — mean={self.mean}, std_dev={self.std_dev}"
