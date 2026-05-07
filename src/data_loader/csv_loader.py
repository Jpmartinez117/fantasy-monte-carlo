"""CSV implementation of PlayerDataProvider."""

import csv
import io
import math
from pathlib import Path
from typing import List, Tuple

from src.models.player import Player, VALID_POSITIONS
from src.data_loader.base import PlayerDataProvider, DataLoadError

EXPECTED_HEADER = ["Name", "Position", "Mean", "StdDev"]


class CsvPlayerProvider(PlayerDataProvider):
    """Loads player data from a local CSV file.

    The file must have exactly the header: Name,Position,Mean,StdDev
    Rows that fail validation are skipped and reported as warnings.
    Duplicate (Name, Position) pairs keep the first occurrence.

    Args:
        file_path: Path to the CSV file (str or Path).

    Example:
        provider = CsvPlayerProvider("data/players.csv")
        players = provider.load_players()
    """

    def __init__(self, file_path):
        self._path = Path(file_path)

    def load_players(self) -> List[Player]:
        if not self._path.exists():
            raise DataLoadError(f"File not found: {self._path}")

        try:
            # utf-8-sig transparently strips a UTF-8 BOM if present.  Excel,
            # Google Sheets, and Notepad++ all add a BOM by default, so this
            # silently accepts those exports instead of failing the header check.
            raw_text = self._path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            # Convert the cryptic UnicodeDecodeError into a DataLoadError so
            # the CLI surfaces a friendly message instead of a traceback.
            raise DataLoadError(
                f"File is not valid UTF-8: {self._path}. "
                f"Re-save the CSV as UTF-8 and try again."
            ) from exc
        except OSError as exc:
            raise DataLoadError(f"Cannot read file {self._path}: {exc}") from exc

        rows, warnings = _parse_csv(raw_text)
        for w in warnings:
            print(f"[WARNING] {w}")

        return rows


# ---------------------------------------------------------------------------
# Internal helpers — not part of the public API
# ---------------------------------------------------------------------------

def _parse_csv(text: str) -> Tuple[List[Player], List[str]]:
    """Parse CSV text and return (players, warnings).

    Line numbers in messages are 1-based and include the header row.
    """
    players: List[Player] = []
    warnings: List[str] = []
    seen: set = set()  # (name, position) pairs already accepted

    # Feed the reader a file-like object instead of a pre-split list of lines.
    # csv.reader needs the underlying stream to correctly join multi-line
    # quoted fields (e.g. "Smith\nJr.") into a single cell.  reader.line_num
    # gives the actual file line number for accurate warning messages.
    reader = csv.reader(io.StringIO(text))

    # -- Header ---------------------------------------------------------------
    try:
        header = next(reader)
    except StopIteration:
        raise DataLoadError("CSV file is empty")

    if header != EXPECTED_HEADER:
        raise DataLoadError(
            f"Bad header: expected {EXPECTED_HEADER}, got {header}"
        )

    # -- Data rows ------------------------------------------------------------
    for raw_row in reader:
        # reader.line_num is the file-line number of the row we just consumed
        # (1-based, header was line 1).  Using it instead of an enumerate
        # counter keeps line numbers correct even for multi-line quoted fields.
        line_num = reader.line_num
        if not any(raw_row):  # skip blank lines
            continue
        if len(raw_row) != 4:
            warnings.append(
                f"Line {line_num}: column count {len(raw_row)} (expected 4) — skipped"
            )
            continue

        row_dict = dict(zip(EXPECTED_HEADER, raw_row))

        try:
            player = _validate_row(row_dict, line_num)
        except ValueError as exc:
            warnings.append(str(exc))
            continue

        key = (player.name, player.position)
        if key in seen:
            warnings.append(
                f"Line {line_num}: Duplicate player "
                f"(Name={player.name!r}, Position={player.position!r}) — skipped"
            )
            continue

        seen.add(key)
        players.append(player)

    return players, warnings


def _validate_row(row: dict, line_num: int) -> Player:
    """Validate a single row dict and return a Player, or raise ValueError."""
    name = str(row["Name"]).strip()
    position = str(row["Position"]).strip().upper()
    mean_raw = str(row["Mean"]).strip()
    stddev_raw = str(row["StdDev"]).strip()

    if not name:
        raise ValueError(f"Line {line_num}: Name is empty")

    if not position:
        raise ValueError(f"Line {line_num}: Position is empty")

    if position not in VALID_POSITIONS:
        raise ValueError(
            f"Line {line_num}: Invalid Position {position!r} "
            f"(allowed: {','.join(sorted(VALID_POSITIONS))})"
        )

    mean = _parse_float(mean_raw, "Mean", line_num)
    std_dev = _parse_float(stddev_raw, "StdDev", line_num)

    if not (0 <= mean <= 60):
        raise ValueError(f"Line {line_num}: Mean {mean} out of range (0–60)")

    if not (0 <= std_dev <= 25):
        raise ValueError(f"Line {line_num}: StdDev {std_dev} out of range (0–25)")

    return Player(name=name, position=position, mean=mean, std_dev=std_dev)


def _parse_float(value: str, field: str, line_num: int) -> float:
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ValueError(
            f"Line {line_num}: {field} is non-numeric {value!r}"
        )

    if not math.isfinite(result):
        raise ValueError(f"Line {line_num}: {field} must not be NaN or Infinity")

    return result
