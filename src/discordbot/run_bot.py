import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from src.discordbot.commands import setup_commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


if __name__ == "__main__":
    load_dotenv()

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user} (ID: {bot.user.id if bot.user else 'unknown'})")
        print("------")
        await bot.tree.sync()
        print("Command tree synced!")
        print("------")

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN environment variable is not set")

    setup_commands(bot)

    bot.run(token)
