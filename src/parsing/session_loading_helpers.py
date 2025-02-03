import csv
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from src.parsing.schemas.session import PokerSession


def parse_utc_datetime(dt_str: str) -> datetime:
    """Parse datetime string in UTC format"""
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def cents_to_dollars(cents: str) -> Decimal:
    """Convert cents to dollars, handling None values"""
    return Decimal(cents) / 100


def load_sessions(csv_path: Path) -> List[PokerSession]:
    """
    Load poker sessions from a CSV file into a list of PokerSession models

    Args:
        csv_path: Path to the CSV file containing poker session data

    Returns:
        List of PokerSession objects
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at {csv_path}")

    sessions: List[PokerSession] = []

    with csv_path.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            session = PokerSession(
                player_nickname=row["player_nickname"],
                player_id=row["player_id"],
                session_start_at=parse_utc_datetime(row["session_start_at"]),
                session_end_at=parse_utc_datetime(row["session_end_at"])
                if row["session_end_at"]
                else None,
                buy_in_dollars=cents_to_dollars(row["buy_in"]),
                buy_out_dollars=cents_to_dollars(row["buy_out"])
                if row["buy_out"]
                else None,
                stack_dollars=cents_to_dollars(row["stack"]),
                net_dollars=cents_to_dollars(row["net"]),
            )
            sessions.append(session)

    return sessions


def load_starting_data(csv_path: str | Path) -> dict[str, Decimal]:
    """
    Load starting balances from CSV file

    Args:
        csv_path: Path to the starting data CSV file

    Returns:
        Dictionary mapping player names to their starting balances
    """
    starting_data: dict[str, Decimal] = {}
    with open(csv_path) as f:
        # Check if file has content
        first_line = f.readline()
        if not first_line:  # File is empty
            return starting_data

        # Process remaining lines
        for line in f:
            if not line.strip():  # Skip empty lines
                continue
            name, net = line.strip().split(",")
            starting_data[name] = Decimal(net)

    return starting_data


def get_csv_files_from_directory(directory: str) -> list[Path]:
    csv_files: list[Path] = []
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            csv_files.append(Path(filepath))
    return csv_files


def merge_player_data(
    current_data: dict[str, Decimal],
    additional_data: dict[str, Decimal],
    fill_missing: bool = True,
) -> dict[str, Decimal]:
    """
    Merges two player data dictionaries and adjusts values.

    Args:
        current_data: Primary dictionary of player data
        additional_data: Secondary dictionary to merge/add
        fill_missing: If True, adds missing players with 0 value
    """
    result = current_data.copy()

    # Add missing players with zero value
    if fill_missing:
        for player in additional_data:
            if player not in result:
                result[player] = Decimal("0")

    # Add additional data values
    for player in result:
        if player in additional_data:
            result[player] += additional_data[player]

    return result


def load_all_sessions(ledgers_dir: str) -> List[PokerSession]:
    """
    Loads and combines all poker sessions from CSV files in a directory.

    Args:
        ledgers_dir: Directory path containing session CSV files

    Returns:
        List of all sessions combined
    """
    all_sessions: List[PokerSession] = []
    filepaths = get_csv_files_from_directory(ledgers_dir)
    for filepath in filepaths:
        sessions = load_sessions(Path(filepath))
        all_sessions.extend(sessions)
    return all_sessions
