from typing import List

from discord.ext import commands

from src.analytics.analytics_helpers import get_all_player_nets
from src.config import LEDGERS_DIR, STARTING_DATA_PATH
from src.parsing.schemas.session import PokerSession
from src.parsing.session_loading_helpers import (
    load_all_sessions,
    load_starting_data,
    merge_player_data,
)


async def graph_all_player_nets(ctx: commands.Context[commands.Bot]):
    all_sessions: List[PokerSession] = []
    ledgers_dir = LEDGERS_DIR
    all_sessions = load_all_sessions(ledgers_dir)

    player_nets = get_all_player_nets(all_sessions)
    starting_data = load_starting_data(STARTING_DATA_PATH)
    player_nets = merge_player_data(player_nets, starting_data)

    # Sort players by net in descending order
    sorted_players_descending = sorted(
        player_nets.items(), key=lambda x: x[1], reverse=True
    )

    result_msg = "\n".join(
        f"{player}: ${abs(net):,.2f} {'DOWN' if net < 0 else 'UP'}"
        for player, net in sorted_players_descending
    )

    await ctx.send(result_msg)


def setup_commands(bot: commands.Bot):
    bot.add_command(
        commands.Command(graph_all_player_nets, name="graph_all_player_nets")
    )
