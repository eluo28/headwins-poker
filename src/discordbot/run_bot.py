import logging

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from config.discord_config import DiscordConfig
from src.get_secret import get_secret

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.CheckFailure):
        logger.error(f"Permission check failed: {error}")
        await interaction.response.send_message(
            f"You must have role {DiscordConfig.HEADWINSPOKER_ADMIN_ROLE_NAME} to use this command.",
            ephemeral=True,
        )
    else:
        logger.error(f"Unexpected error in command: {error}")
        await interaction.response.send_message(
            "An error occurred while processing the command.", ephemeral=True
        )


@bot.event
async def on_ready():
    logger.info(
        f"Logged in as {bot.user} (ID: {bot.user.id if bot.user else 'unknown'})"
    )

    # Load cogs and sync commands after bot is ready
    await bot.load_extension("src.discordbot.cogs.graph_commands")
    await bot.load_extension("src.discordbot.cogs.ledger_and_log_commands")
    await bot.load_extension("src.discordbot.cogs.starting_data_commands")
    await bot.tree.sync()

    logger.info("Cogs loaded and commands synced")
    logger.info("------")


@bot.command()
@commands.has_role(DiscordConfig.HEADWINSPOKER_ADMIN_ROLE_NAME)
async def reload(ctx: commands.Context[commands.Bot]):
    """Reload all cogs and sync commands"""
    try:
        # Reload all extensions
        await bot.reload_extension("src.discordbot.cogs.graph_commands")
        await bot.reload_extension("src.discordbot.cogs.ledger_and_log_commands")
        await bot.reload_extension("src.discordbot.cogs.starting_data_commands")
        await bot.tree.sync()

        logger.info("Cogs reloaded and commands synced")
        await ctx.send("All cogs reloaded and commands synced!", ephemeral=True)
    except Exception as e:
        logger.error(f"Error reloading cogs: {e}")
        await ctx.send("Error reloading cogs", ephemeral=True)


if __name__ == "__main__":
    load_dotenv()
    token = get_secret("discord_token")
    bot.run(token)
