from io import BytesIO
from logging import getLogger
from typing import Literal

import boto3
import discord

from src.config.aws_config import AWSConfig

logger = getLogger(__name__)

FileType = Literal["registered_players", "ledgers", "logs"]


class S3Service:
    def __init__(self) -> None:
        self.s3_client = boto3.client("s3")
        self.bucket_name: str = AWSConfig.BUCKET_NAME

    def _get_prefix(self, guild_id: str, file_type: FileType) -> str:
        """Get the S3 prefix for a given file type and guild."""
        return f"uploads/{guild_id}/{file_type}/"

    async def get_file(self, guild_id: str, filename: str, file_type: FileType) -> tuple[bool, str]:
        """
        Get a specific file from S3.
        Returns (success, message)
        """
        try:
            key = self._get_prefix(guild_id, file_type) + filename
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return True, response["Body"].read().decode("utf-8")
        except Exception as e:
            logger.error(f"Error getting {file_type} file: {e}")
            return False, f"Failed to get {filename}"

    async def list_files(self, guild_id: str, file_type: FileType, limit: int | None = None) -> tuple[list[str], str]:
        """
        List files of a specific type in S3 for a guild.
        Args:
            guild_id: The Discord guild ID
            file_type: Type of files to list
            limit: Maximum number of files to return, ordered by last modified date. If None, returns all files.
        Returns (list of filenames, message)
        """
        try:
            prefix = self._get_prefix(guild_id, file_type)
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

            if "Contents" not in response:
                return [], f"No {file_type} files found"

            # Get filenames and sort by last modified
            files = sorted(
                [{"name": obj["Key"].split("/")[-1], "modified": obj["LastModified"]} for obj in response["Contents"]],
                key=lambda x: x["modified"],
                reverse=True,
            )

            if not files:
                return [], f"No {file_type} files found"

            # Apply limit if specified
            if limit is not None:
                files = files[:limit]

            file_list = [
                f"{i + 1}. {f['name']} (modified: {f['modified'].strftime('%Y-%m-%d %H:%M:%S')})"
                for i, f in enumerate(files)
            ]

            message = f"{file_type.title()} files:\n" + "\n".join(file_list)
            return [f["name"] for f in files], message

        except Exception as e:
            logger.error(f"Error listing {file_type} files: {e}")
            return [], f"Failed to list {file_type} files"

    async def delete_file(self, guild_id: str, filename: str, file_type: FileType) -> tuple[bool, str]:
        """
        Delete a specific file from S3.
        Returns (success, message)
        """
        try:
            key = self._get_prefix(guild_id, file_type) + filename
            logger.info(f"Attempting to delete {file_type} file: {key}")

            # Check if file exists
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            except self.s3_client.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    message = f"File '{filename}' not found"
                    logger.info(message)
                    return False, message
                else:
                    raise

            # Delete the file
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True, f"Successfully deleted {filename}"

        except Exception as e:
            logger.error(f"Error deleting {file_type} file: {e}")
            return False, f"Failed to delete {filename}"

    async def upload_file(
        self,
        file: discord.Attachment,
        guild_id: str,
        file_type: FileType,
    ) -> tuple[bool, str]:
        """
        Upload a single file to S3.
        Returns (success, message)
        """
        try:
            file_content = await file.read()
            file_buffer = BytesIO(file_content)
            key = self._get_prefix(guild_id, file_type) + file.filename

            self.s3_client.upload_fileobj(
                file_buffer,
                self.bucket_name,
                key,
                ExtraArgs={"ContentType": "text/csv"},
            )
            return True, f"Successfully uploaded {file.filename}"

        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {e}")
            return False, f"Failed to upload {file.filename}"
