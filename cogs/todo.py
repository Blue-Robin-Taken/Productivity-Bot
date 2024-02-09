# --- This is the To-Do Cog for commands related to To-Do ---

import discord
from discord.ext import commands


class ToDo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    to_do_group = discord.SlashCommandGroup("to-do")

    @to_do_group.command()
    async def create(self, ctx,
                     name: discord.Option(description="The name for your to-do list.", required=True, min_length=1,
                                          max_length=10)):
        await ctx.respond(f"Created the list `{name}`!")


def setup(bot):
    bot.add_cog(ToDo(bot))
