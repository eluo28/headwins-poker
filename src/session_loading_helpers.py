import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

from src.schemas.session import PokerSession


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
        next(f)  # Skip header
        for line in f:
            name, net = line.strip().split(",")
            starting_data[name] = Decimal(net)
    return starting_data
