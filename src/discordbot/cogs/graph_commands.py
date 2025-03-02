from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.analytics.visualizations import (
    fetch_consolidated_sessions_and_registered_players,
    get_file_object_of_player_nets_over_time,
    get_file_object_of_player_played_time_totals,
    get_file_object_of_player_profit_per_hour,
)
from src.discordbot.services.s3_service import S3Service

logger = getLogger(__name__)


class GraphCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="graph_all_player_nets",
        description="Generates a graph showing all players' net profits over time",
    )
    async def graph_all_player_nets(self, interaction: discord.Interaction) -> None:
        logger.info(f"Graphing all player nets for guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Loading all ledger sessions and registered players for guild {interaction.guild_id}")

            consolidated_sessions, registered_players = await fetch_consolidated_sessions_and_registered_players(
                str(interaction.guild_id), S3Service()
            )

            file_object = get_file_object_of_player_nets_over_time(consolidated_sessions, registered_players)
            discord_file = discord.File(file_object, filename="player_nets_over_time.png")

            await interaction.followup.send(file=discord_file)
        except Exception as e:
            logger.error(f"Other error: {e}")
            try:
                await interaction.followup.send(f"An error occurred: {e!s}", ephemeral=True)
            except Exception as e:
                logger.error(f"Could not send error message: {e}")

    @app_commands.command(
        name="graph_played_time_totals",
        description="Generates a graph showing all players' total time played",
    )
    async def graph_all_player_played_time_totals(self, interaction: discord.Interaction) -> None:
        logger.info(f"Graphing all player played time totals for guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Loading all ledger sessions and registered players for guild {interaction.guild_id}")

            all_consolidated_sessions, registered_players = await fetch_consolidated_sessions_and_registered_players(
                str(interaction.guild_id), S3Service()
            )

            file_object = get_file_object_of_player_played_time_totals(all_consolidated_sessions, registered_players)
            discord_file = discord.File(file_object, filename="player_played_time_totals.png")

            await interaction.followup.send(file=discord_file)
        except Exception as e:
            logger.error(f"Other error: {e}")
            try:
                await interaction.followup.send(f"An error occurred: {e!s}", ephemeral=True)
            except Exception as e:
                logger.error(f"Could not send error message: {e}")

    @app_commands.command(
        name="graph_profit_per_hour",
        description="Generates a graph showing all players' profit per hour played",
    )
    async def graph_profit_per_hour(self, interaction: discord.Interaction) -> None:
        logger.info(f"Graphing profit per hour for guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Loading all ledger sessions and registered players for guild {interaction.guild_id}")

            consolidated_sessions, registered_players = await fetch_consolidated_sessions_and_registered_players(
                str(interaction.guild_id), S3Service()
            )

            file_object = get_file_object_of_player_profit_per_hour(consolidated_sessions, registered_players)
            discord_file = discord.File(file_object, filename="profit_per_hour.png")

            await interaction.followup.send(file=discord_file)
        except Exception as e:
            logger.error(f"Other error: {e}")
            try:
                await interaction.followup.send(f"An error occurred: {e!s}", ephemeral=True)
            except Exception as e:
                logger.error(f"Could not send error message: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GraphCommands(bot))
