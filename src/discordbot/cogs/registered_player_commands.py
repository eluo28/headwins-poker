from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config.discord_config import DiscordConfig
from src.discordbot.helpers.validation_helpers import validate_registered_players_file
from discordbot.services.s3_service import S3Service

logger = getLogger(__name__)


class RegisteredPlayerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, s3_service: S3Service) -> None:
        self.bot = bot
        self.s3_service = s3_service

    @app_commands.command(
        name="upload_registered_players",
        description="Upload registered players JSON file with player balances in the format of player_name,net_amount,date",
    )
    async def upload_registered_players(
        self,
        interaction: discord.Interaction,
        registered_players_file: discord.Attachment,
    ) -> None:
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Uploading registered players JSON file: {registered_players_file.filename}")

            validation_result = await validate_registered_players_file(registered_players_file)
            if validation_result:
                await interaction.followup.send(validation_result, ephemeral=True)
                return

            success, message = await self.s3_service.upload_file(registered_players_file, str(interaction.guild_id), "registered_players")
            await interaction.followup.send(message, ephemeral=not success)

        except Exception as e:
            logger.error(f"Error in upload_registered_players: {e}")
            await interaction.followup.send("An error occurred while uploading the file.", ephemeral=True)

    @app_commands.command(
        name="list_registered_players",
        description="List last 10 registered players JSON files that have been uploaded, ordered by last modified date",
    )
    async def list_registered_players(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Listing registered players files for guild {interaction.guild_id}")

            files, message = await self.s3_service.list_files(str(interaction.guild_id), "registered_players", limit=10)
            await interaction.followup.send(message, ephemeral=len(files) == 0)

        except Exception as e:
            logger.error(f"Error in list_registered_players: {e}")
            await interaction.followup.send("An error occurred while listing files.", ephemeral=True)

    @app_commands.command(
        name="delete_registered_players",
        description="Delete a registered players JSON file",
    )
    @app_commands.checks.has_role(DiscordConfig.HEADWINSPOKER_ADMIN_ROLE_NAME)
    async def delete_registered_players(
        self,
        interaction: discord.Interaction,
        filename: str,
    ) -> None:
        logger.info(f"Deleting registered players file {filename} for guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Deleting registered players file {filename} for guild {interaction.guild_id}")

            # First check if file exists
            files, _ = await self.s3_service.list_files(str(interaction.guild_id), "registered_players")
            if filename not in files:
                await interaction.followup.send(
                    f"File '{filename}' not found in registered players files.",
                    ephemeral=True,
                )
                return

            success, message = await self.s3_service.delete_file(str(interaction.guild_id), filename, "registered_players")
            await interaction.followup.send(message, ephemeral=not success)

        except Exception as e:
            logger.error(f"Error in delete_registered_players: {e}")
            await interaction.followup.send("An error occurred while deleting the file.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RegisteredPlayerCommands(bot, S3Service()))
