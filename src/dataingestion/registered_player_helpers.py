import json
from logging import getLogger

from src.dataingestion.schemas.registered_player import InitialDetails, RegisteredPlayer
from src.discordbot.services.s3_service import S3Service

logger = getLogger(__name__)


async def load_registered_players(guild_id: str, s3_service: S3Service) -> list[RegisteredPlayer]:
    """
    Load player mappings from JSON in S3 and return ID and nickname mappings.

    Args:
        guild_id: Discord guild ID to load player mappings for

    Returns:
        Tuple of (id_to_name, nickname_to_name) mapping dicts
    """
    logger.info(f"Loading registered players for guild {guild_id}")

    registered_players: list[RegisteredPlayer] = []

    try:
        success, file_content = await s3_service.get_file(guild_id, "registered_players.json", "registered_players")
        if not success:
            raise Exception(file_content)

        registered_players_json = json.loads(file_content)

        for player_name, player_data in registered_players_json.items():
            registered_players.append(
                RegisteredPlayer(
                    player_name_lowercase=player_name.lower(),
                    player_ids=player_data["played_ids"],
                    player_nicknames_lowercase=[nick.lower() for nick in player_data["played_nicknames"]],
                    initial_details=InitialDetails(
                        initial_net_amount=player_data["initial_details"]["initial_net_amount"],
                        initial_date=player_data["initial_details"]["initial_date"],
                    )
                    if "initial_details" in player_data
                    else None,
                )
            )

        return registered_players

    except Exception as e:
        logger.error(f"Error loading player mapping from S3: {e}")
        return []
