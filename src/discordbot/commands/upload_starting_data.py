import re
from io import BytesIO
from logging import getLogger

import boto3
import discord

from src.config.aws_config import AWSConfig

logger = getLogger(__name__)


@discord.app_commands.command(
    name="upload_starting_data",
    description="Upload starting data CSV file with player balances in the format of player_name,net_amount,date",
)
async def upload_starting_data(
    interaction: discord.Interaction,
    starting_data_file: discord.Attachment,
):
    try:
        await interaction.response.defer(thinking=True)
        logger.info(f"Uploading starting data CSV file: {starting_data_file.filename}")

        validation_result = await validate_starting_data_file(starting_data_file)
        if validation_result:
            await interaction.followup.send(validation_result, ephemeral=True)
            return

        s3 = boto3.client("s3")
        bucket_name = AWSConfig.BUCKET_NAME

        # Read file content
        file_content = await starting_data_file.read()
        file_buffer = BytesIO(file_content)

        # Upload to S3
        try:
            s3.upload_fileobj(
                file_buffer,
                bucket_name,
                f"uploads/{interaction.guild_id}/starting_data/{starting_data_file.filename}",
                ExtraArgs={"ContentType": "text/csv"},
            )
            await interaction.followup.send(
                f"Successfully uploaded starting data: {starting_data_file.filename}"
            )
        except Exception as e:
            logger.error(f"Failed to upload {starting_data_file.filename}: {e}")
            await interaction.followup.send(
                "Failed to upload starting data file.", ephemeral=True
            )

    except Exception as e:
        logger.error(f"Error in upload_starting_data: {e}")
        await interaction.followup.send(
            "An error occurred while uploading the file.", ephemeral=True
        )


async def validate_starting_data_file(file: discord.Attachment) -> str | None:
    """Validate the starting data CSV file format."""
    if not file.filename.endswith(".csv"):
        return "Please upload a CSV file"

    content = await file.read()
    text = content.decode("utf-8")
    lines = text.strip().split("\n")

    # Check each line format
    for i, line in enumerate(lines):
        parts = line.strip().split(",")
        if len(parts) != 3:
            return f"Line {i + 1} should have exactly 3 columns: player_name,net_amount,date"

        try:
            # Validate net amount is a number
            float(parts[1])
        except ValueError:
            return f"Invalid net amount on line {i + 1}: {parts[1]}"

        try:
            # Validate date format (YYYY-MM-DD)
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", parts[2].strip()):
                raise ValueError
        except ValueError:
            return f"Invalid date format on line {i + 1}. Expected YYYY-MM-DD"

    return None
