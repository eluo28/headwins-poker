from discord.ext import commands

from src.discordbot.commands.graph_all_player_nets import graph_all_player_nets
from src.discordbot.commands.upload_ledger_and_log_csv import upload_ledger_and_log_csv
from src.discordbot.commands.upload_starting_data import upload_starting_data


def setup_commands(bot: commands.Bot):
    bot.tree.add_command(graph_all_player_nets)
    bot.tree.add_command(upload_ledger_and_log_csv)
    bot.tree.add_command(upload_starting_data)
