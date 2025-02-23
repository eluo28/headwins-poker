from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from config.discord_config import DiscordConfig
from src.discordbot.helpers.validation_helpers import validate_csv_files
from src.discordbot.services.s3_service import S3Service

logger = getLogger(__name__)


class LedgerAndLogCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, s3_service: S3Service):
        self.bot = bot
        self.s3_service = s3_service

    @app_commands.command(
        name="upload_ledger_and_log_csv",
        description="Upload ledger and log CSV files to store poker game data",
    )
    async def upload_ledger_and_log_csv(
        self,
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

            uploaded_files, message = await self.s3_service.upload_ledger_and_log(
                ledger_file, log_file, str(interaction.guild_id)
            )
            await interaction.followup.send(message, ephemeral=len(uploaded_files) == 0)

        except Exception as e:
            logger.error(f"Error in upload_csv: {e}")
            await interaction.followup.send(
                "An error occurred while uploading files.", ephemeral=True
            )

    @app_commands.command(
        name="list_ledger_files",
        description="List last 10 ledger CSV files that have been uploaded, ordered by last modified date",
    )
    async def list_ledger_files(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Listing ledger files for guild {interaction.guild_id}")

            files, message = await self.s3_service.list_files(
                str(interaction.guild_id), "ledgers", limit=10
            )
            await interaction.followup.send(message, ephemeral=len(files) == 0)

        except Exception as e:
            logger.error(f"Error in list_ledger_files: {e}")
            await interaction.followup.send(
                "An error occurred while listing files.", ephemeral=True
            )

    @app_commands.command(
        name="list_log_files",
        description="List last 10 log CSV files that have been uploaded, ordered by last modified date",
    )
    async def list_log_files(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Listing log files for guild {interaction.guild_id}")

            files, message = await self.s3_service.list_files(
                str(interaction.guild_id), "logs", limit=10
            )
            await interaction.followup.send(message, ephemeral=len(files) == 0)

        except Exception as e:
            logger.error(f"Error in list_log_files: {e}")
            await interaction.followup.send(
                "An error occurred while listing files.", ephemeral=True
            )

    @app_commands.command(
        name="delete_ledger_file",
        description="Delete a specific ledger CSV file",
    )
    @app_commands.checks.has_role(DiscordConfig.HEADWINSPOKER_ADMIN_ROLE_NAME)
    async def delete_ledger_file(
        self,
        interaction: discord.Interaction,
        filename: str,
    ):
        try:
            await interaction.response.defer(thinking=True)
            logger.info(
                f"Deleting ledger file {filename} for guild {interaction.guild_id}"
            )

            files, _ = await self.s3_service.list_files(
                str(interaction.guild_id), "ledgers"
            )
            if filename not in files:
                await interaction.followup.send(
                    f"File '{filename}' not found in ledger files.",
                    ephemeral=True,
                )
                return

            success, message = await self.s3_service.delete_file(
                str(interaction.guild_id), filename, "ledgers"
            )
            await interaction.followup.send(message, ephemeral=not success)

        except Exception as e:
            logger.error(f"Error in delete_ledger_file: {e}")
            await interaction.followup.send(
                "An error occurred while deleting the file.", ephemeral=True
            )

    @app_commands.command(
        name="delete_log_file",
        description="Delete a specific log CSV file",
    )
    @app_commands.checks.has_role(DiscordConfig.HEADWINSPOKER_ADMIN_ROLE_NAME)
    async def delete_log_file(
        self,
        interaction: discord.Interaction,
        filename: str,
    ):
        try:
            await interaction.response.defer(thinking=True)
            logger.info(
                f"Deleting log file {filename} for guild {interaction.guild_id}"
            )

            files, _ = await self.s3_service.list_files(
                str(interaction.guild_id), "logs"
            )
            if filename not in files:
                await interaction.followup.send(
                    f"File '{filename}' not found in log files.",
                    ephemeral=True,
                )
                return

            success, message = await self.s3_service.delete_file(
                str(interaction.guild_id), filename, "logs"
            )
            await interaction.followup.send(message, ephemeral=not success)

        except Exception as e:
            logger.error(f"Error in delete_log_file: {e}")
            await interaction.followup.send(
                "An error occurred while deleting the file.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(LedgerAndLogCommands(bot, S3Service()))
