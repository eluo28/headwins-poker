import csv
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from logging import getLogger
from pathlib import Path
from typing import List

import boto3

from src.config.aws_config import AWSConfig
from src.parsing.schemas.session import PokerSession
from src.parsing.schemas.starting_data_entry import StartingDataEntry

logger = getLogger(__name__)


def parse_utc_datetime(dt_str: str) -> datetime:
    """Parse datetime string in UTC format"""
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def cents_to_dollars(cents: str) -> Decimal:
    """Convert cents to dollars, handling None values"""
    return Decimal(cents) / 100


def load_sessions(csv_file: StringIO) -> List[PokerSession]:
    """
    Load poker sessions from a CSV file or StringIO into a list of PokerSession models

    Args:
        csv_path: Path to CSV file or StringIO containing CSV data

    Returns:
        List of PokerSession objects
    """
    # First pass: read all rows into memory
    rows = []

    reader = csv.DictReader(csv_file)
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
            player_nickname_lowercase=row["player_nickname"].lower(),
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


def load_starting_data(guild_id: str) -> List[StartingDataEntry]:
    """
    Load starting balances from CSV file in S3

    Args:
        guild_id: Discord guild ID to load starting data for

    Returns:
        List of StartingDataEntry objects containing player starting balances
    """
    s3 = boto3.client("s3")
    bucket_name = AWSConfig.BUCKET_NAME
    prefix = f"uploads/{guild_id}/starting_data/"

    starting_data: List[StartingDataEntry] = []
    try:
        # Get the most recent starting data file
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" not in response:
            logger.warning(f"No starting data found for guild {guild_id}")
            return starting_data

        # Sort by last modified and get the most recent file
        latest_file = sorted(
            response["Contents"], key=lambda x: x["LastModified"], reverse=True
        )[0]

        # Get the file content
        file_obj = s3.get_object(Bucket=bucket_name, Key=latest_file["Key"])
        file_content = file_obj["Body"].read().decode("utf-8")

        # Parse each line
        for line in file_content.strip().split("\n"):
            name, net, date_str = line.strip().split(",")
            entry = StartingDataEntry(
                player_name_lowercase=name.lower(),
                net_dollars=Decimal(net),
                date=date.fromisoformat(date_str),
            )
            starting_data.append(entry)

    except Exception as e:
        logger.error(f"Error loading starting data from S3: {e}")
        raise

    return starting_data


def get_ledger_csv_paths_and_contents_from_s3_for_guild(
    guild_id: str,
) -> list[tuple[Path, StringIO]]:
    """
    Gets paths and contents of ledger CSV files from S3 for a guild.

    Args:
        guild_id: Discord guild ID to get files for

    Returns:
        List of tuples containing (Path, StringIO) for each CSV file
    """
    s3 = boto3.client("s3")
    bucket_name = AWSConfig.BUCKET_NAME
    prefix = AWSConfig.LEDGER_PREFIX.format(guild_id=guild_id)

    csv_files: list[tuple[Path, StringIO]] = []
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" in response:
            for obj in response["Contents"]:
                if obj["Key"].endswith(".csv"):
                    # Get the object from S3
                    file_obj = s3.get_object(Bucket=bucket_name, Key=obj["Key"])
                    # Read the file content
                    file_content = file_obj["Body"].read().decode("utf-8")
                    # Create a StringIO object
                    csv_file = StringIO(file_content)
                    csv_files.append((Path(obj["Key"]), csv_file))
    except Exception as e:
        logger.error(f"Error accessing S3: {e}")
        raise

    return csv_files


def load_all_ledger_sessions(guild_id: str) -> List[PokerSession]:
    """
    Loads and combines all poker sessions from CSV files in S3.

    Args:
        guild_id: Discord guild ID to load sessions for

    Returns:
        List of all sessions combined
    """
    all_sessions: List[PokerSession] = []

    for _, csv_file in get_ledger_csv_paths_and_contents_from_s3_for_guild(guild_id):
        sessions = load_sessions(csv_file)
        all_sessions.extend(sessions)

    return all_sessions
