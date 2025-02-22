from discord.ext import commands

from src.discordbot.commands.graph_all_player_nets import graph_all_player_nets
from src.discordbot.commands.upload_ledger_and_log_csv import upload_ledger_and_log_csv


def setup_commands(bot: commands.Bot):
    bot.tree.add_command(graph_all_player_nets)
    bot.tree.add_command(upload_ledger_and_log_csv)
