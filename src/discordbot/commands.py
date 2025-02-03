from typing import List

import discord
from discord.ext import commands

from src.analytics.visualizations import get_file_object_of_player_nets_over_time
from src.config import LEDGERS_DIR, STARTING_DATA_PATH
from src.parsing.schemas.session import PokerSession
from src.parsing.session_loading_helpers import load_all_sessions, load_starting_data


async def graph_all_player_nets(ctx: commands.Context[commands.Bot]):
    all_sessions: List[PokerSession] = []
    ledgers_dir = LEDGERS_DIR
    all_sessions = load_all_sessions(ledgers_dir)

    starting_data = load_starting_data(STARTING_DATA_PATH)

    file_object = get_file_object_of_player_nets_over_time(all_sessions, starting_data)

    discord_file = discord.File(file_object, filename="player_nets_over_time.png")

    await ctx.send(file=discord_file)


def setup_commands(bot: commands.Bot):
    bot.add_command(
        commands.Command(graph_all_player_nets, name="graph_all_player_nets")
    )
