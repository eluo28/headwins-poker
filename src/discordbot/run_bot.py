import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

from src.get_secret import get_secret

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)


@bot.event
async def on_ready():
    logger.info(
        f"Logged in as {bot.user} (ID: {bot.user.id if bot.user else 'unknown'})"
    )

    # Load cogs and sync commands after bot is ready
    await bot.load_extension("src.discordbot.cogs.graph")
    await bot.load_extension("src.discordbot.cogs.upload")
    await bot.tree.sync()

    logger.info("Cogs loaded and commands synced")
    logger.info("------")


if __name__ == "__main__":
    load_dotenv()
    token = get_secret("discord_token")
    bot.run(token)
