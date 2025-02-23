from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.discordbot.helpers.s3_helpers import (
    delete_starting_data_file,
    list_starting_data_files,
    upload_starting_data_to_s3,
)
from src.discordbot.helpers.validation_helpers import validate_starting_data_file

logger = getLogger(__name__)


class StartingDataCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="upload_starting_data",
        description="Upload starting data CSV file with player balances in the format of player_name,net_amount,date",
    )
    async def upload_starting_data(
        self,
        interaction: discord.Interaction,
        starting_data_file: discord.Attachment,
    ):
        try:
            await interaction.response.defer(thinking=True)
            logger.info(
                f"Uploading starting data CSV file: {starting_data_file.filename}"
            )

            validation_result = await validate_starting_data_file(starting_data_file)
            if validation_result:
                await interaction.followup.send(validation_result, ephemeral=True)
                return

            success, message = await upload_starting_data_to_s3(
                starting_data_file, str(interaction.guild_id)
            )
            await interaction.followup.send(message, ephemeral=not success)

        except Exception as e:
            logger.error(f"Error in upload_starting_data: {e}")
            await interaction.followup.send(
                "An error occurred while uploading the file.", ephemeral=True
            )

    @app_commands.command(
        name="list_starting_data",
        description="List all starting data CSV files that have been uploaded",
    )
    async def list_starting_data(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Listing starting data files for guild {interaction.guild_id}")

            files, message = await list_starting_data_files(str(interaction.guild_id))
            await interaction.followup.send(message, ephemeral=len(files) == 0)

        except Exception as e:
            logger.error(f"Error in list_starting_data: {e}")
            await interaction.followup.send(
                "An error occurred while listing files.", ephemeral=True
            )

    @app_commands.command(
        name="delete_starting_data",
        description="Delete a specific starting data CSV file",
    )
    async def delete_starting_data(
        self,
        interaction: discord.Interaction,
        filename: str,
    ):
        try:
            await interaction.response.defer(thinking=True)
            logger.info(
                f"Deleting starting data file {filename} for guild {interaction.guild_id}"
            )

            # First check if file exists
            files, _ = await list_starting_data_files(str(interaction.guild_id))
            if filename not in files:
                await interaction.followup.send(
                    f"File '{filename}' not found in starting data files.",
                    ephemeral=True,
                )
                return

            success, message = await delete_starting_data_file(
                str(interaction.guild_id), filename
            )
            await interaction.followup.send(message, ephemeral=not success)

        except Exception as e:
            logger.error(f"Error in delete_starting_data: {e}")
            await interaction.followup.send(
                "An error occurred while deleting the file.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(StartingDataCommands(bot))
