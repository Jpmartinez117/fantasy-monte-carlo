def validate_player_row(row):
    """
    Validate and clean a single CSV row representing a fantasy football player.

    Args:
        row (dict): A dictionary with keys Name, Position, Mean, StdDev.

    Returns:
        dict: Cleaned and validated player data.

    Raises:
        ValueError: If the row is missing fields or contains invalid values.
    """
    if not isinstance(row, dict):
        raise ValueError("Each CSV row must be a dictionary")

    required_fields = ["Name", "Position", "Mean", "StdDev"]

    for field in required_fields:
        if field not in row:
            raise ValueError(f"Missing required field: '{field}'")

    name_value = row["Name"]
    position_value = row["Position"]
    mean_value = row["Mean"]
    stddev_value = row["StdDev"]

    name = "" if name_value is None else str(name_value).strip()
    position = "" if position_value is None else str(position_value).strip().upper()
    mean_raw = "" if mean_value is None else str(mean_value).strip()
    stddev_raw = "" if stddev_value is None else str(stddev_value).strip()

    if not name:
        raise ValueError("Player Name cannot be empty or whitespace")

    if not position:
        raise ValueError("Player Position cannot be empty or whitespace")

    valid_positions = {"QB", "RB", "WR", "TE"}
    if position not in valid_positions:
        raise ValueError(
            f"Invalid position: {position!r}. Must be one of {sorted(valid_positions)}"
        )

    try:
        mean = float(mean_raw)
    except (ValueError, TypeError):
        raise ValueError(f"Mean must be a valid number, got: {row['Mean']!r}")

    try:
        std_dev = float(stddev_raw)
    except (ValueError, TypeError):
        raise ValueError(f"StdDev must be a valid number, got: {row['StdDev']!r}")

    if mean < 0:
        raise ValueError(f"Mean cannot be negative: {mean}")

    if std_dev < 0:
        raise ValueError(f"StdDev cannot be negative: {std_dev}")

    return {
        "Name": name,
        "Position": position,
        "Mean": mean,
        "StdDev": std_dev,
    }