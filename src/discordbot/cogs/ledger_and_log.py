from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.discordbot.helpers.s3_helpers import (
    delete_ledger_file,
    delete_log_file,
    list_ledger_files,
    list_log_files,
    upload_ledger_and_log_to_s3,
)
from src.discordbot.helpers.validation_helpers import validate_csv_files

logger = getLogger(__name__)


class LedgerAndLogCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

            uploaded_files, message = await upload_ledger_and_log_to_s3(
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
        description="List all ledger CSV files that have been uploaded",
    )
    async def list_ledger_files(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Listing ledger files for guild {interaction.guild_id}")

            files, message = await list_ledger_files(str(interaction.guild_id))
            await interaction.followup.send(message, ephemeral=len(files) == 0)

        except Exception as e:
            logger.error(f"Error in list_ledger_files: {e}")
            await interaction.followup.send(
                "An error occurred while listing files.", ephemeral=True
            )

    @app_commands.command(
        name="list_log_files",
        description="List all log CSV files that have been uploaded",
    )
    async def list_log_files(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Listing log files for guild {interaction.guild_id}")

            files, message = await list_log_files(str(interaction.guild_id))
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

            files, _ = await list_ledger_files(str(interaction.guild_id))
            if filename not in files:
                await interaction.followup.send(
                    f"File '{filename}' not found in ledger files.",
                    ephemeral=True,
                )
                return

            success, message = await delete_ledger_file(
                str(interaction.guild_id), filename
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

            files, _ = await list_log_files(str(interaction.guild_id))
            if filename not in files:
                await interaction.followup.send(
                    f"File '{filename}' not found in log files.",
                    ephemeral=True,
                )
                return

            success, message = await delete_log_file(
                str(interaction.guild_id), filename
            )
            await interaction.followup.send(message, ephemeral=not success)

        except Exception as e:
            logger.error(f"Error in delete_log_file: {e}")
            await interaction.followup.send(
                "An error occurred while deleting the file.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(LedgerAndLogCommands(bot))
