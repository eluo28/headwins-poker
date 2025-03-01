from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.discordbot.services.s3_service import S3Service
from src.analytics.visualizations import get_file_object_of_player_nets_over_time
from src.dataingestion.ledger_session_helpers import (
    load_all_ledger_sessions,
)
from src.dataingestion.registered_player_helpers import load_registered_players

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
            logger.info(f"Loading all ledger sessions for guild {interaction.guild_id}")

            all_sessions = await load_all_ledger_sessions(str(interaction.guild_id), S3Service())
            logger.info(f"Loaded {len(all_sessions)} player ledger sessions")

            registered_players = await load_registered_players(str(interaction.guild_id), S3Service())
            logger.info(f"Loaded {len(registered_players)} registered players")

            if not all_sessions:
                await interaction.followup.send("No sessions found", ephemeral=True)
                return

            file_object = get_file_object_of_player_nets_over_time(all_sessions, registered_players)
            discord_file = discord.File(file_object, filename="player_nets_over_time.png")

            await interaction.followup.send(file=discord_file)
        except discord.errors.NotFound as e:
            logger.error(f"Interaction error: {e}")
        except Exception as e:
            logger.error(f"Other error: {e}")
            try:
                await interaction.followup.send(f"An error occurred: {e!s}", ephemeral=True)
            except Exception as e:
                logger.error(f"Could not send error message: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GraphCommands(bot))
