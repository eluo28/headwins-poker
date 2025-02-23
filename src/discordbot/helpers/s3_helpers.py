from io import BytesIO
from logging import getLogger
from typing import Literal

import boto3
import discord

from src.config.aws_config import AWSConfig

logger = getLogger(__name__)

FileType = Literal["starting_data", "ledgers", "logs"]


def get_s3_prefix(guild_id: str, file_type: FileType) -> str:
    """Get the S3 prefix for a given file type and guild."""
    return f"uploads/{guild_id}/{file_type}/"


async def list_s3_files(guild_id: str, file_type: FileType) -> tuple[list[str], str]:
    """
    List all files of a specific type in S3 for a guild.
    Returns (list of filenames, message)
    """
    try:
        s3 = boto3.client("s3")
        bucket_name = AWSConfig.BUCKET_NAME
        prefix = get_s3_prefix(guild_id, file_type)

        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

        if "Contents" not in response:
            return [], f"No {file_type} files found"

        # Get filenames and sort by last modified
        files = sorted(
            [
                {"name": obj["Key"].split("/")[-1], "modified": obj["LastModified"]}
                for obj in response["Contents"]
                if obj["Key"].endswith(".csv")
            ],
            key=lambda x: x["modified"],
            reverse=True,
        )

        if not files:
            return [], f"No {file_type} files found"

        file_list = [
            f"{i + 1}. {f['name']} (modified: {f['modified'].strftime('%Y-%m-%d %H:%M:%S')})"
            for i, f in enumerate(files)
        ]

        message = f"{file_type.title()} files:\n" + "\n".join(file_list)
        return [f["name"] for f in files], message

    except Exception as e:
        logger.error(f"Error listing {file_type} files: {e}")
        return [], f"Failed to list {file_type} files"


async def delete_s3_file(
    guild_id: str, filename: str, file_type: FileType
) -> tuple[bool, str]:
    """
    Delete a specific file from S3.
    Returns (success, message)
    """
    try:
        s3 = boto3.client("s3")
        bucket_name = AWSConfig.BUCKET_NAME
        key = get_s3_prefix(guild_id, file_type) + filename

        # Check if file exists
        try:
            s3.head_object(Bucket=bucket_name, Key=key)
        except s3.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False, f"File '{filename}' not found"
            else:
                raise

        # Delete the file
        s3.delete_object(Bucket=bucket_name, Key=key)
        return True, f"Successfully deleted {filename}"

    except Exception as e:
        logger.error(f"Error deleting {file_type} file: {e}")
        return False, f"Failed to delete {filename}"


# Convenience functions that use the generic functions above
async def list_starting_data_files(guild_id: str) -> tuple[list[str], str]:
    return await list_s3_files(guild_id, "starting_data")


async def list_ledger_files(guild_id: str) -> tuple[list[str], str]:
    return await list_s3_files(guild_id, "ledgers")


async def list_log_files(guild_id: str) -> tuple[list[str], str]:
    return await list_s3_files(guild_id, "logs")


async def delete_starting_data_file(guild_id: str, filename: str) -> tuple[bool, str]:
    return await delete_s3_file(guild_id, filename, "starting_data")


async def delete_ledger_file(guild_id: str, filename: str) -> tuple[bool, str]:
    return await delete_s3_file(guild_id, filename, "ledgers")


async def delete_log_file(guild_id: str, filename: str) -> tuple[bool, str]:
    return await delete_s3_file(guild_id, filename, "logs")


async def upload_starting_data_to_s3(
    starting_data_file: discord.Attachment, guild_id: str
) -> tuple[bool, str]:
    """
    Upload starting data file to S3.
    Returns (success, message)
    """
    try:
        s3 = boto3.client("s3")
        bucket_name = AWSConfig.BUCKET_NAME

        # Read file content
        file_content = await starting_data_file.read()
        file_buffer = BytesIO(file_content)

        # Upload to S3
        s3.upload_fileobj(
            file_buffer,
            bucket_name,
            f"uploads/{guild_id}/starting_data/{starting_data_file.filename}",
            ExtraArgs={"ContentType": "text/csv"},
        )
        return (
            True,
            f"Successfully uploaded starting data: {starting_data_file.filename}",
        )

    except Exception as e:
        logger.error(f"Failed to upload {starting_data_file.filename}: {e}")
        return False, "Failed to upload starting data file."


async def upload_ledger_and_log_to_s3(
    ledger_file: discord.Attachment, log_file: discord.Attachment, guild_id: str
) -> tuple[list[str], str]:
    """
    Upload ledger and log files to S3.
    Returns (list of uploaded files, message)
    """
    s3 = boto3.client("s3")
    bucket_name = AWSConfig.BUCKET_NAME
    uploaded_files = []

    for file in [ledger_file, log_file]:
        # Read file content
        file_content = await file.read()
        file_buffer = BytesIO(file_content)
        folder_type = "ledgers" if file == ledger_file else "logs"

        try:
            s3.upload_fileobj(
                file_buffer,
                bucket_name,
                f"uploads/{guild_id}/{folder_type}/{file.filename}",
                ExtraArgs={"ContentType": "text/csv"},
            )
            uploaded_files.append(file.filename)
        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {e}")
            continue

    if uploaded_files:
        message = f"Successfully uploaded {len(uploaded_files)} files: {', '.join(uploaded_files)}"
    else:
        message = "No CSV files were uploaded successfully."

    return uploaded_files, message
