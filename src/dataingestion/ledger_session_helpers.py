import csv
from decimal import Decimal
from io import StringIO
from logging import getLogger
from pathlib import Path

import boto3

from src.config.aws_config import AWSConfig
from src.dataingestion.common_utils import cents_to_dollars, parse_utc_datetime
from src.dataingestion.schemas.consolidated_session import ConsolidatedPlayerSession
from src.dataingestion.schemas.player_mapping_details import PlayerMappingDetails
from src.dataingestion.schemas.player_session_log import PlayerSessionLog

logger = getLogger(__name__)


def load_sessions_from_csv_file(csv_file: StringIO) -> list[PlayerSessionLog]:
    """
    Load poker sessions from a CSV file or StringIO into a list of PlayerSessionLog models

    Args:
        csv_path: Path to CSV file or StringIO containing CSV data

    Returns:
        List of PlayerSessionLog objects
    """
    # First pass: read all rows into memory
    rows = []

    reader = csv.DictReader(csv_file)
    rows = list(reader)

    sessions: list[PlayerSessionLog] = []

    for i, row in enumerate(rows):
        # Try to get adjacent row timestamps
        prev_start = (
            parse_utc_datetime(rows[i - 1]["session_start_at"]) if i > 0 and rows[i - 1]["session_start_at"] else None
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

        session = PlayerSessionLog(
            player_nickname_lowercase=row["player_nickname"].lower(),
            player_id=row["player_id"],
            session_start_at=start_time,
            session_end_at=parse_utc_datetime(row["session_end_at"]) if row["session_end_at"] else None,
            buy_in_dollars=cents_to_dollars(row["buy_in"]),
            buy_out_dollars=cents_to_dollars(row["buy_out"]) if row["buy_out"] else None,
            stack_dollars=cents_to_dollars(row["stack"]),
            net_dollars=cents_to_dollars(row["net"]),
        )
        sessions.append(session)

    return sessions


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


def load_all_ledger_sessions(guild_id: str) -> list[PlayerSessionLog]:
    """
    Loads and combines all poker sessions from CSV files in S3.

    Args:
        guild_id: Discord guild ID to load sessions for

    Returns:
        list of all sessions combined
    """
    all_sessions: list[PlayerSessionLog] = []

    for _, csv_file in get_ledger_csv_paths_and_contents_from_s3_for_guild(guild_id):
        sessions = load_sessions_from_csv_file(csv_file)
        all_sessions.extend(sessions)

    return all_sessions


def consolidate_sessions_with_player_mapping_details(
    session_logs: list[PlayerSessionLog], player_mapping_details: list[PlayerMappingDetails]
) -> list[ConsolidatedPlayerSession]:
    consolidated_sessions: list[ConsolidatedPlayerSession] = []

    # First consolidate based on player mapping details
    for player_mapping_detail in player_mapping_details:
        net_dollars = Decimal(0)
        date = None
        for session_log in session_logs:
            if (
                session_log.player_id in player_mapping_detail.player_ids
                or session_log.player_nickname_lowercase in player_mapping_detail.player_nicknames_lowercase
            ):
                net_dollars += session_log.net_dollars
                if date is None:
                    date = session_log.session_start_at.date()

        if date is None:
            raise ValueError(f"No date found for player {player_mapping_detail.player_name_lowercase}")

        if net_dollars != 0:  # Only add if they have activity
            consolidated_sessions.append(
                ConsolidatedPlayerSession(
                    player_nickname_lowercase=player_mapping_detail.player_name_lowercase,
                    net_dollars=net_dollars,
                    date=date,
                )
            )

    # Then consolidate any remaining unmapped nicknames
    processed_nicknames = {
        nickname for detail in player_mapping_details for nickname in detail.player_nicknames_lowercase
    }

    # Group unmapped sessions by nickname and consolidate
    unmapped_sessions = {}
    for session_log in session_logs:
        if session_log.player_nickname_lowercase not in processed_nicknames:
            if session_log.player_nickname_lowercase not in unmapped_sessions:
                unmapped_sessions[session_log.player_nickname_lowercase] = {
                    "net_dollars": Decimal(0),
                    "date": session_log.session_start_at.date(),
                }
            unmapped_sessions[session_log.player_nickname_lowercase]["net_dollars"] += session_log.net_dollars

    # Add consolidated unmapped sessions
    for nickname, data in unmapped_sessions.items():
        consolidated_sessions.append(
            ConsolidatedPlayerSession(
                player_nickname_lowercase=nickname,
                net_dollars=data["net_dollars"],
                date=data["date"],
            )
        )
        processed_nicknames.add(nickname)

    return consolidated_sessions
