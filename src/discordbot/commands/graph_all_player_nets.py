from logging import getLogger

import discord

from src.analytics.visualizations import get_file_object_of_player_nets_over_time
from src.parsing.session_loading_helpers import (
    load_all_ledger_sessions,
    load_starting_data,
)

logger = getLogger(__name__)


@discord.app_commands.command(
    name="graph_all_player_nets",
    description="Generates a graph showing all players' net profits over time",
)
async def graph_all_player_nets(interaction: discord.Interaction):
    try:
        await interaction.response.defer(thinking=True)  # Shows "Bot is thinking..."

        all_sessions = load_all_ledger_sessions(str(interaction.guild_id))
        starting_data = load_starting_data(str(interaction.guild_id))
        file_object = get_file_object_of_player_nets_over_time(
            all_sessions, starting_data
        )
        discord_file = discord.File(file_object, filename="player_nets_over_time.png")

        await interaction.followup.send(file=discord_file)
    except discord.errors.NotFound as e:
        print(f"Interaction error: {e}")
    except Exception as e:
        print(f"Other error: {e}")
        try:
            await interaction.followup.send(
                f"An error occurred: {str(e)}", ephemeral=True
            )
        except Exception as e:
            print(f"Could not send error message: {e}")
