"""Abstract base class for all player data providers."""

from abc import ABC, abstractmethod
from typing import List

from src.models.player import Player


class PlayerDataProvider(ABC):
    """Interface that every data source must implement.

    Concrete implementations (CSV file, REST API, database, etc.) each
    subclass this and fill in load_players().  The rest of the application
    only ever calls load_players() so the source can be swapped without
    touching simulation or CLI code.
    """

    @abstractmethod
    def load_players(self) -> List[Player]:
        """Load and return a validated list of Player objects.

        Returns:
            A list of Player instances ready for simulation.

        Raises:
            DataLoadError: If the source cannot be read or contains
                           unrecoverable errors.
        """


class DataLoadError(Exception):
    """Raised when a data provider fails to load player data."""
