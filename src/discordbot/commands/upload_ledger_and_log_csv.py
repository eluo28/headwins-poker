from io import BytesIO
from logging import getLogger

import boto3
import discord

from src.config.aws_config import AWSConfig

logger = getLogger(__name__)


@discord.app_commands.command(
    name="upload_ledger_and_log_csv",
    description="Upload ledger and log CSV files to store poker game data",
)
async def upload_ledger_and_log_csv(
    interaction: discord.Interaction,
    ledger_file: discord.Attachment,
    log_file: discord.Attachment,
):
    try:
        await interaction.response.defer(thinking=True)
        logger.info(
            f"Uploading ledger and log CSV files: {ledger_file.filename} and {log_file.filename}"
        )

        validation_result = await validate_csv_files(ledger_file, log_file)
        if validation_result:
            await interaction.followup.send(validation_result, ephemeral=True)
            return

        s3 = boto3.client("s3")
        bucket_name = AWSConfig.BUCKET_NAME
        uploaded_files = []

        for file in [ledger_file, log_file]:
            # Read file content
            file_content = await file.read()
            file_buffer = BytesIO(file_content)
            folder_type = "ledgers" if file == ledger_file else "logs"
            # Upload to S3
            try:
                s3.upload_fileobj(
                    file_buffer,
                    bucket_name,
                    f"uploads/{interaction.guild_id}/{folder_type}/{file.filename}",
                    ExtraArgs={"ContentType": "text/csv"},
                )
                uploaded_files.append(file.filename)
            except Exception as e:
                logger.error(f"Failed to upload {file.filename}: {e}")
                continue

        if uploaded_files:
            await interaction.followup.send(
                f"Successfully uploaded {len(uploaded_files)} files: {', '.join(uploaded_files)}"
            )
        else:
            await interaction.followup.send(
                "No CSV files were uploaded successfully.", ephemeral=True
            )

    except Exception as e:
        logger.error(f"Error in upload_csv: {e}")
        await interaction.followup.send(
            "An error occurred while uploading files.", ephemeral=True
        )


async def validate_ledger_file(ledger_file: discord.Attachment) -> str | None:
    if not ledger_file.filename.endswith(".csv") or not ledger_file.filename.startswith(
        "ledger"
    ):
        return "Please upload a ledger CSV file starting with 'ledger'"

    ledger_content = await ledger_file.read()
    ledger_text = ledger_content.decode("utf-8")
    first_line = ledger_text.split("\n")[0].strip()
    expected_headers = "player_nickname,player_id,session_start_at,session_end_at,buy_in,buy_out,stack,net"

    if first_line != expected_headers:
        return "Ledger CSV file must have the following headers: player_nickname,player_id,session_start_at,session_end_at,buy_in,buy_out,stack,net"

    return None


async def validate_log_file(log_file: discord.Attachment) -> str | None:
    if not log_file.filename.endswith(".csv") or not log_file.filename.startswith(
        "poker_now_log"
    ):
        return "Please upload a log CSV file starting with 'poker_now_log'"

    log_content = await log_file.read()
    log_text = log_content.decode("utf-8")
    log_first_line = log_text.split("\n")[0].strip()
    expected_log_headers = "entry,at,order"

    if log_first_line != expected_log_headers:
        return "Log CSV file must have the following headers: entry,at,order"

    return None


async def validate_csv_files(
    ledger_file: discord.Attachment, log_file: discord.Attachment
) -> str | None:
    ledger_validation = await validate_ledger_file(ledger_file)
    if ledger_validation:
        return ledger_validation

    log_validation = await validate_log_file(log_file)
    if log_validation:
        return log_validation

    return None
