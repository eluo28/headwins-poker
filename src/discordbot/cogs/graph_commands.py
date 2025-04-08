from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.dataingestion.registered_player_helpers import load_registered_players
from src.dataingestion.poker_hand_parser import load_all_poker_logs
from src.analytics.ledger_visualizations import (
    fetch_consolidated_sessions_and_registered_players,
    get_file_object_of_buy_in_analysis,
    get_file_object_of_player_nets_over_time,
    get_file_object_of_player_played_time_totals,
    get_file_object_of_player_profit_per_hour,
)
from src.analytics.log_visualizations import (
    get_file_object_of_total_vpip,
    get_file_object_of_vpip_over_time,
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

    @app_commands.command(
        name="graph_buy_in_analysis",
        description="Analyzes the relationship between buy-in amounts and final results",
    )
    async def graph_buy_in_analysis(self, interaction: discord.Interaction) -> None:
        logger.info(f"Generating buy-in analysis for guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Loading all ledger sessions and registered players for guild {interaction.guild_id}")

            consolidated_sessions, _ = await fetch_consolidated_sessions_and_registered_players(
                str(interaction.guild_id), S3Service()
            )

            file_object = get_file_object_of_buy_in_analysis(consolidated_sessions)
            discord_file = discord.File(file_object, filename="buy_in_analysis.png")

            await interaction.followup.send(file=discord_file)
        except Exception as e:
            logger.error(f"Error in buy-in analysis: {e}")
            try:
                await interaction.followup.send(f"An error occurred: {e!s}", ephemeral=True)
            except Exception as e:
                logger.error(f"Could not send error message: {e}")


    @app_commands.command(
        name="graph_total_vpip",
        description="Generates a graph showing VPIP (Voluntarily Put Money In Pot) percentage for each player",
    )
    async def graph_total_vpip(self, interaction: discord.Interaction) -> None:
        logger.info(f"Graphing VPIP percentages for guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Loading poker hands for guild {interaction.guild_id}")

            registered_players = await load_registered_players(str(interaction.guild_id), S3Service())
            # Load hands from S3
            logs = await load_all_poker_logs(str(interaction.guild_id), S3Service(), registered_players)

            if not logs:
                await interaction.followup.send("No poker hand data available yet.", ephemeral=True)
                return

            file_object = get_file_object_of_total_vpip(logs)
            discord_file = discord.File(file_object, filename="vpip_analysis.png")

            await interaction.followup.send(file=discord_file)
        except Exception as e:
            logger.error(f"Error in VPIP analysis: {e}")
            try:
                await interaction.followup.send(f"An error occurred: {e!s}", ephemeral=True)
            except Exception as e:
                logger.error(f"Could not send error message: {e}")

    @app_commands.command(
        name="graph_vpip_by_session",
        description="Generates a graph showing how each player's VPIP percentage changes over time",
    )
    @app_commands.describe(
        num_sessions="Number of most recent sessions to include (optional, defaults to all sessions)"
    )
    async def graph_vpip_by_session(
        self, 
        interaction: discord.Interaction,
        num_sessions: int
    ) -> None:
        logger.info(f"Graphing VPIP percentages over time for guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Loading poker hands for guild {interaction.guild_id}")

            registered_players = await load_registered_players(str(interaction.guild_id), S3Service())
            # Load hands from S3
            logs = await load_all_poker_logs(str(interaction.guild_id), S3Service(), registered_players)

            if not logs:
                await interaction.followup.send("No poker hand data available yet.", ephemeral=True)
                return

            file_object = get_file_object_of_vpip_over_time(logs, num_sessions)
            discord_file = discord.File(file_object, filename="vpip_over_time.png")

            await interaction.followup.send(file=discord_file)
        except Exception as e:
            logger.error(f"Error in VPIP over time analysis: {e}")
            try:
                await interaction.followup.send(f"An error occurred: {e!s}", ephemeral=True)
            except Exception as e:
                logger.error(f"Could not send error message: {e}")

    @app_commands.command(
        name="graph_latest_session_vpip",
        description="Generates a graph showing VPIP percentages for each player in the most recent session",
    )
    async def graph_latest_session_vpip(self, interaction: discord.Interaction) -> None:
        logger.info(f"Graphing VPIP percentages for latest session in guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Loading poker hands for guild {interaction.guild_id}")

            registered_players = await load_registered_players(str(interaction.guild_id), S3Service())
            # Load hands from S3
            logs = await load_all_poker_logs(str(interaction.guild_id), S3Service(), registered_players)

            if not logs:
                await interaction.followup.send("No poker hand data available yet.", ephemeral=True)
                return
                
            # Sort logs by date and get the latest one
            sorted_logs = sorted(logs, key=lambda x: x.date)
            latest_log = sorted_logs[-1]
            
            # Use the existing function with just the latest log
            file_object = get_file_object_of_total_vpip([latest_log])
            discord_file = discord.File(file_object, filename="latest_session_vpip.png")

            await interaction.followup.send(file=discord_file)
        except Exception as e:
            logger.error(f"Error in latest session VPIP analysis: {e}")
            try:
                await interaction.followup.send(f"An error occurred: {e!s}", ephemeral=True)
            except Exception as e:
                logger.error(f"Could not send error message: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GraphCommands(bot))
