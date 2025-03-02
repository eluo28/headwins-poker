from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

logger = getLogger(__name__)


class HelpCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Get help on how to use the HeadWins Poker bot",
    )
    async def help_command(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(thinking=True)
            logger.info(f"Sending help information for guild {interaction.guild_id}")

            # Create an embed for the help message
            embed = discord.Embed(
                title="Headwins Poker Bot Help",
                description="This bot helps you track and analyze your poker games with friends. Here's how to use it:",
                color=discord.Color.blue()
            )

            # Registered Players section
            embed.add_field(
                name="📋 Registered Players",
                value=(
                    "To consolidate your players' information (if the same player plays under different nicknames), "
                    "or if you want to add initial details to a player's record, "
                    "upload a JSON file with your players' information using `/upload_registered_players`.\n\n"
                    "**Format Example:**\n"
                    "```json\n"
                    "{\n"
                    '    "PlayerName": {\n'
                    '        "played_ids": ["player_id_1", "player_id_2"],\n'
                    '        "played_nicknames": ["nickname1", "nickname2"],\n'
                    '        "initial_details": {\n'
                    '            "initial_net_amount": 100.50,\n'
                    '            "initial_date": "YYYY-MM-DD"\n'
                    '        }\n'
                    "    },\n"
                    '    "AnotherPlayer": {\n'
                    '        "played_ids": ["another_id"],\n'
                    '        "played_nicknames": ["another_nickname"],\n'
                    '        "initial_details": {\n'
                    '            "initial_net_amount": -50.25,\n'
                    '            "initial_date": "YYYY-MM-DD"\n'
                    '        }\n'
                    "    }\n"
                    "}\n"
                    "```\n"
                    "- `played_ids`: IDs from PokerNow that identify this player\n"
                    "- `played_nicknames`: Nicknames used by this player\n"
                    "- `initial_details`: Starting balance and date (optional)\n"
                ),
                inline=False
            )

            # Ledger and Log Files section
            embed.add_field(
                name="📊 Ledger and Log Files",
                value=(
                    "After each poker session, upload the CSV files from PokerNow using `/upload_ledger_and_log_csv`.\n\n"
                    "**Steps:**\n"
                    "1. At the end of your PokerNow game, download both the **Ledger CSV** and **Hand Log CSV**\n"
                    "2. Use the `/upload_ledger_and_log_csv` command and attach both files\n"
                    "3. The bot will process and store these files for analysis\n\n"
                    "These files contain all the information about your poker session, including player balances, "
                    "hands played, and game actions."
                ),
                inline=False
            )

            # Analysis Commands section
            embed.add_field(
                name="📈 Analysis Commands",
                value=(
                    "Once you've uploaded your data, use these commands to analyze your games:\n\n"
                    "- `/graph_all_player_nets` - View all players' net profits over time\n"
                    "- `/graph_played_time_totals` - See how much time each player has spent playing\n"
                    "- `/graph_profit_per_hour` - Analyze each player's profit per hour played\n"
                ),
                inline=False
            )

            # File Management section
            embed.add_field(
                name="🗂️ File Management",
                value=(
                    "You can manage your uploaded files with these commands, only admins "
                    "(users with a role named `headwins_admin`) can delete files:\n\n"
                    "- `/list_ledger_files` - View uploaded ledger files\n"
                    "- `/list_log_files` - View uploaded log files\n"
                    "- `/list_registered_players` - View uploaded registered players files\n"
                    "- `/get_registered_players` - Fetch your current registered players file\n"
                    "- `/delete_ledger_file` - Delete a specific ledger file by name (admin only)\n"
                    "- `/delete_log_file` - Delete a specific log file by name (admin only)\n"
                    "- `/delete_registered_players` - Delete the registered players file (admin only)\n"
                ),
                inline=False
            )

            # Send the embed
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in help_command: {e}")
            await interaction.followup.send("An error occurred while sending help information.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCommands(bot)) 