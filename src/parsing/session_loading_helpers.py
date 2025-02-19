import csv
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from src.parsing.schemas.session import PokerSession
from src.parsing.schemas.starting_data_entry import StartingDataEntry


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

    # First pass: read all rows into memory
    rows = []
    with csv_path.open("r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    sessions: List[PokerSession] = []

    for i, row in enumerate(rows):
        # Try to get adjacent row timestamps
        prev_start = (
            parse_utc_datetime(rows[i - 1]["session_start_at"])
            if i > 0 and rows[i - 1]["session_start_at"]
            else None
        )
        next_start = (
            parse_utc_datetime(rows[i + 1]["session_start_at"])
            if i < len(rows) - 1 and rows[i + 1]["session_start_at"]
            else None
        )

        # If current row has no start time, use adjacent start time
        start_time = None
        if row["session_start_at"]:
            start_time = parse_utc_datetime(row["session_start_at"])
        elif prev_start:
            start_time = prev_start
        elif next_start:
            start_time = next_start
        else:
            raise ValueError(f"No start time found for row {i}")

        session = PokerSession(
            player_nickname=row["player_nickname"].lower(),
            player_id=row["player_id"],
            session_start_at=start_time,
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


def load_starting_data(csv_path: str | Path) -> List[StartingDataEntry]:
    """
    Load starting balances from CSV file

    Args:
        csv_path: Path to the starting data CSV file

    Returns:
        List of StartingDataEntry objects containing player starting balances
    """
    starting_data: List[StartingDataEntry] = []
    with open(csv_path) as f:
        for line in f:
            name, net, date_str = line.strip().split(",")
            entry = StartingDataEntry(
                player_name_lowercase=name.lower(),
                net_dollars=Decimal(net),
                date=date.fromisoformat(date_str),
            )
            starting_data.append(entry)

    return starting_data


def get_csv_files_from_directory(directory: str) -> list[Path]:
    csv_files: list[Path] = []
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            csv_files.append(Path(filepath))
    return csv_files


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
