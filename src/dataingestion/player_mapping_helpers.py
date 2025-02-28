import json
from logging import getLogger

import boto3

from src.config.aws_config import AWSConfig
from src.dataingestion.schemas.player_mapping_details import PlayerMappingDetails

logger = getLogger(__name__)


def load_player_mapping(guild_id: str) -> list[PlayerMappingDetails]:
    """
    Load player mappings from JSON in S3 and return ID and nickname mappings.

    Args:
        guild_id: Discord guild ID to load player mappings for

    Returns:
        Tuple of (id_to_name, nickname_to_name) mapping dicts
    """
    s3 = boto3.client("s3")
    bucket_name = AWSConfig.BUCKET_NAME
    key = f"uploads/{guild_id}/player_mapping.json"

    player_mapping_details: list[PlayerMappingDetails] = []

    try:
        file_obj = s3.get_object(Bucket=bucket_name, Key=key)
        file_content = file_obj["Body"].read().decode("utf-8")
        player_mapping = json.loads(file_content)

        for name, data in player_mapping.items():
            name_lower = name.lower()
            player_mapping_details.append(
                PlayerMappingDetails(
                    player_name_lowercase=name_lower,
                    player_ids=[player_id.strip() for player_id in data["played_ids"].split(",")],
                    player_nicknames_lowercase=[
                        nickname.lower().strip() for nickname in data["played_nicknames"].split(",")
                    ],
                )
            )

    except Exception as e:
        logger.error(f"Error loading player mapping from S3: {e}")
        raise

    return player_mapping_details
