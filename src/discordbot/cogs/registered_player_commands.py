from io import BytesIO
from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config.discord_config import DiscordConfig
from src.discordbot.helpers.validation_helpers import validate_registered_players_file
from src.discordbot.services.s3_service import S3Service

logger = getLogger(__name__)


class RegisteredPlayerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, s3_service: S3Service) -> None:
        self.bot = bot
        self.s3_service = s3_service

    @app_commands.command(
        name="upload_registered_players",
        description="Upload registered players JSON file, see /help for more information",
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

            success, message = await self.s3_service.upload_file(
                registered_players_file, str(interaction.guild_id), "registered_players"
            )
            await interaction.followup.send(message, ephemeral=not success)

        except Exception as e:
            logger.error(f"Error in upload_registered_players: {e}")
            await interaction.followup.send("An error occurred while uploading the file.", ephemeral=True)

    @app_commands.command(
        name="get_registered_players",
        description="Get the registered players JSON file",
    )
    async def get_registered_players(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Getting registered players file for guild {interaction.guild_id}")

            success, content = await self.s3_service.get_file(
                str(interaction.guild_id), filename="registered_players.json", file_type="registered_players"
            )

            if not success:
                await interaction.followup.send(content, ephemeral=True)
                return

            file = discord.File(
                BytesIO(content.encode()),
                filename="registered_players.json",
                description="Current registered players file",
            )
            await interaction.followup.send(file=file)

        except Exception as e:
            logger.error(f"Error in get_registered_players: {e}")
            await interaction.followup.send("An error occurred while getting the file.", ephemeral=True)

    @app_commands.command(
        name="list_registered_players",
        description="List all registered players files",
    )
    async def list_registered_players(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Listing registered players files for guild {interaction.guild_id}")

            files, _ = await self.s3_service.list_files(str(interaction.guild_id), "registered_players")

            if not files:
                await interaction.followup.send("No registered players files found.", ephemeral=True)
                return

            file_list = "\n".join(files)
            await interaction.followup.send(f"Registered players files:\n```\n{file_list}\n```")

        except Exception as e:
            logger.error(f"Error in list_registered_players: {e}")
            await interaction.followup.send("An error occurred while listing the files.", ephemeral=True)

    @app_commands.command(
        name="delete_registered_players",
        description="Delete a registered players JSON file",
    )
    @app_commands.checks.has_role(DiscordConfig.HEADWINSPOKER_ADMIN_ROLE_NAME)
    async def delete_registered_players(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This command can only be used in a server", ephemeral=True)
            return

        logger.info(f"Deleting registered players file for guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)

            success, message = await self.s3_service.delete_file(
                str(interaction.guild_id), "registered_players.json", "registered_players"
            )
            await interaction.followup.send(message, ephemeral=not success)

        except Exception as e:
            logger.error(f"Error in delete_registered_players: {e}")
            await interaction.followup.send("An error occurred while deleting the file.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RegisteredPlayerCommands(bot, S3Service()))
