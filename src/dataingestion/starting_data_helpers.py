from datetime import date
from decimal import Decimal
from logging import getLogger

import boto3

from src.config.aws_config import AWSConfig
from src.dataingestion.schemas.starting_data_entry import StartingDataEntry

logger = getLogger(__name__)


def load_starting_data(guild_id: str) -> list[StartingDataEntry]:
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

    starting_data: list[StartingDataEntry] = []
    try:
        # Get the most recent starting data file
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" not in response:
            logger.warning(f"No starting data found for guild {guild_id}")
            return starting_data

        # Sort by last modified and get the most recent file
        latest_file = sorted(response["Contents"], key=lambda x: x["LastModified"], reverse=True)[0]

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
