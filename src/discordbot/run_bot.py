import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

from src.discordbot.commands import setup_commands
from src.get_secret import get_secret

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)

logger = logging.getLogger(__name__)


@bot.event
async def on_ready():
    logger.info(
        f"Logged in as {bot.user} (ID: {bot.user.id if bot.user else 'unknown'})"
    )
    logger.info("------")
    await bot.tree.sync()
    logger.info("Command tree synced!")
    logger.info("------")


if __name__ == "__main__":
    load_dotenv()

    # Get token from environment variable in dev, AWS Secrets Manager in prod
    token = get_secret("discord_token")

    setup_commands(bot)

    bot.run(token)
