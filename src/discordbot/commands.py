from logging import getLogger

import discord
from discord.ext import commands

from src.analytics.visualizations import get_file_object_of_player_nets_over_time
from src.config import LEDGERS_DIR, STARTING_DATA_PATH
from src.parsing.session_loading_helpers import load_all_sessions, load_starting_data

logger = getLogger(__name__)


@discord.app_commands.command(
    name="graph_all_player_nets",
    description="Generates a graph showing all players' net profits over time",
)
async def graph_all_player_nets(interaction: discord.Interaction):
    try:
        # Defer with a loading state
        await interaction.response.defer(thinking=True, ephemeral=False)

        logger.info("Loading sessions and starting data")
        all_sessions = load_all_sessions(LEDGERS_DIR)
        starting_data = load_starting_data(STARTING_DATA_PATH)
        logger.info(
            "Loaded %d sessions and %d starting data entries",
            len(all_sessions),
            len(starting_data),
        )

        logger.info("Generating graph")
        file_object = get_file_object_of_player_nets_over_time(
            all_sessions, starting_data
        )
        discord_file = discord.File(file_object, filename="player_nets_over_time.png")

        logger.info("Sending graph to Discord")
        await interaction.followup.send(file=discord_file)
        logger.info("Graph sent successfully")

    except discord.NotFound as e:
        logger.error("Interaction not found: %s", str(e))
        return
    except Exception as e:
        logger.error("Error in graph_all_player_nets: %s", str(e), exc_info=True)
        try:
            await interaction.followup.send(
                "An error occurred while generating the graph. Please try again.",
                ephemeral=True,
            )
        except discord.NotFound:
            logger.error("Could not send error message - interaction expired")


def setup_commands(bot: commands.Bot):
    bot.tree.add_command(graph_all_player_nets)
