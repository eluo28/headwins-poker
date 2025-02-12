import discord
from discord.ext import commands

from src.analytics.visualizations import get_file_object_of_player_nets_over_time
from src.config import LEDGERS_DIR, STARTING_DATA_PATH
from src.parsing.session_loading_helpers import load_all_sessions, load_starting_data


@discord.app_commands.command(
    name="graph_all_player_nets",
    description="Generates a graph showing all players' net profits over time",
)
async def graph_all_player_nets(interaction: discord.Interaction):
    await interaction.response.defer()
    all_sessions = load_all_sessions(LEDGERS_DIR)
    starting_data = load_starting_data(STARTING_DATA_PATH)
    print(
        f"Loaded {len(all_sessions)} sessions and {len(starting_data)} starting data entries"
    )
    file_object = get_file_object_of_player_nets_over_time(all_sessions, starting_data)
    discord_file = discord.File(file_object, filename="player_nets_over_time.png")

    await interaction.followup.send(file=discord_file)


def setup_commands(bot: commands.Bot):
    bot.tree.add_command(graph_all_player_nets)
