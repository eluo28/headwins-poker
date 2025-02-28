import csv
from decimal import Decimal
from io import StringIO
from logging import getLogger


from src.discordbot.services.s3_service import S3Service
from src.dataingestion.common_utils import cents_to_dollars, parse_utc_datetime
from src.dataingestion.schemas.consolidated_session import ConsolidatedPlayerSession
from src.dataingestion.schemas.player_session_log import PlayerSessionLog
from src.dataingestion.schemas.registered_player import RegisteredPlayer

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


async def get_ledger_csv_file_contents(
    guild_id: str,
    s3_service: S3Service,
) -> list[StringIO]:
    """
    Gets contents of ledger CSV files from S3 for a guild.

    Args:
        guild_id: Discord guild ID to get files for

    Returns:
        List of csv file contents for each ledger CSV file
    """
    csv_files: list[StringIO] = []
    try:
        file_names, _ = await s3_service.list_files(guild_id, "ledgers")
        for file_name in file_names:
            if file_name.endswith(".csv"):
                # Get the object from S3
                success, file_content = await s3_service.get_file(guild_id, file_name, "ledgers")
                if not success:
                    raise Exception(file_content)
                # Create a StringIO object
                csv_file = StringIO(file_content)
                csv_files.append(csv_file)
    except Exception as e:
        logger.error(f"Error accessing S3: {e}")
        raise

    return csv_files


async def load_all_ledger_sessions(guild_id: str, s3_service: S3Service) -> list[PlayerSessionLog]:
    """
    Loads and combines all poker sessions from CSV files in S3.

    Args:
        guild_id: Discord guild ID to load sessions for

    Returns:
        list of all sessions combined
    """
    all_sessions: list[PlayerSessionLog] = []
    csv_files = await get_ledger_csv_file_contents(guild_id, s3_service)

    for csv_file in csv_files:
        sessions = load_sessions_from_csv_file(csv_file)
        all_sessions.extend(sessions)

    return all_sessions


def consolidate_sessions_with_player_mapping_details(
    session_logs: list[PlayerSessionLog], registered_players: list[RegisteredPlayer]
) -> list[ConsolidatedPlayerSession]:
    consolidated_sessions: list[ConsolidatedPlayerSession] = []

    # First consolidate based on registered player details
    for registered_player in registered_players:
        # Group sessions by date for each player
        sessions_by_date = {}
        for session_log in session_logs:
            if (
                session_log.player_id in registered_player.player_ids
                or session_log.player_nickname_lowercase in registered_player.player_nicknames_lowercase
                or session_log.player_nickname_lowercase == registered_player.player_name_lowercase
            ):
                session_date = session_log.session_start_at.date()
                if session_date not in sessions_by_date:
                    sessions_by_date[session_date] = Decimal(0)
                sessions_by_date[session_date] += session_log.net_dollars

        if not sessions_by_date:
            raise ValueError(f"No sessions found for player {registered_player.player_name_lowercase}")

        for date, net_dollars in sessions_by_date.items():
            consolidated_sessions.append(
                ConsolidatedPlayerSession(
                    player_nickname_lowercase=registered_player.player_name_lowercase,
                    net_dollars=net_dollars,
                    date=date,
                )
            )

    # Then consolidate any remaining unmapped nicknames
    processed_player_ids = {
        player_id
        for registered_player in registered_players
        for player_id in registered_player.player_ids
    }

    processed_nicknames = {
        registered_player.player_name_lowercase
        for registered_player in registered_players
    } | {
        nickname
        for registered_player in registered_players
        for nickname in registered_player.player_nicknames_lowercase
    } | {
        session_log.player_nickname_lowercase
        for session_log in session_logs
        if session_log.player_id in processed_player_ids
    }

    # Filter unmapped sessions and sort by nickname and date
    unmapped_sessions = sorted(
        [s for s in session_logs if s.player_nickname_lowercase not in processed_nicknames],
        key=lambda x: (x.player_nickname_lowercase, x.session_start_at.date())
    )

    # Group sessions by nickname and date
    grouped_sessions = {}
    for session in unmapped_sessions:
        nickname = session.player_nickname_lowercase
        date = session.session_start_at.date()
        key = (nickname, date)
        
        if key not in grouped_sessions:
            grouped_sessions[key] = []
        grouped_sessions[key].append(session)

    # Consolidate grouped sessions
    for (nickname, date), sessions in grouped_sessions.items():
        net_dollars = sum(session.net_dollars for session in sessions)
        consolidated_sessions.append(
            ConsolidatedPlayerSession(
                player_nickname_lowercase=nickname,
                net_dollars=Decimal(net_dollars),
                date=date
            )
        )

    return consolidated_sessions
