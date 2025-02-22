import logging

from discord.ext import commands

from src.discordbot.run_bot import bot

logger = logging.getLogger(__name__)


@bot.command()
@commands.is_owner()
async def sync(ctx: commands.Context[commands.Bot]) -> None:
    await bot.tree.sync()
    await ctx.send("Command tree synced.")
