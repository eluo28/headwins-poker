from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.analytics.visualizations import get_file_object_of_player_nets_over_time
from src.parsing.session_loading_helpers import (
    load_all_ledger_sessions,
    load_starting_data,
)

logger = getLogger(__name__)


class Graph(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="graph_all_player_nets",
        description="Generates a graph showing all players' net profits over time",
    )
    async def graph_all_player_nets(self, interaction: discord.Interaction):
        logger.info(f"Graphing all player nets for guild {interaction.guild_id}")
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Loading all ledger sessions for guild {interaction.guild_id}")

            all_sessions = load_all_ledger_sessions(str(interaction.guild_id))
            logger.info(f"Loaded {len(all_sessions)} ledger sessions")

            starting_data = load_starting_data(str(interaction.guild_id))
            logger.info(f"Loaded {len(starting_data)} starting data entries")

            if not all_sessions and not starting_data:
                await interaction.followup.send(
                    "No sessions or starting data found", ephemeral=True
                )
                return

            file_object = get_file_object_of_player_nets_over_time(
                all_sessions, starting_data
            )
            discord_file = discord.File(
                file_object, filename="player_nets_over_time.png"
            )

            await interaction.followup.send(file=discord_file)
        except discord.errors.NotFound as e:
            logger.error(f"Interaction error: {e}")
        except Exception as e:
            logger.error(f"Other error: {e}")
            try:
                await interaction.followup.send(
                    f"An error occurred: {str(e)}", ephemeral=True
                )
            except Exception as e:
                logger.error(f"Could not send error message: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Graph(bot))
