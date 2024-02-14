import discord
from discord.ext import commands
# from discord.ui import View, Button, Modal, InputText
# from discord import InputTextStyle
import asyncio

SECONDS_PER_OPTION = {
    'seconds': 1,
    'minutes': 60,
    'hours': 3600,
    'days': 86400,
    'weeks': 604800
}

# def checkIfTimerStopped():


class Timers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    timer_group = discord.SlashCommandGroup('timer')

    @timer_group.command()
    async def create(self, ctx, seconds: discord.Option(int, required=False) = 0,
                     minutes: discord.Option(int, required=False) = 0,
                     hours: discord.Option(int, required=False) = 0,
                     days: discord.Option(int, required=False) = 0,
                     weeks: discord.Option(int, required=False) = 0):
        # -- Check if no time selected --
        if not (seconds or minutes or hours or days or weeks):
            return await ctx.respond("You have to select a time!", ephemeral=True)

        await ctx.respond("Your timer has started!", ephemeral=True)
        # -- Create timer loop --
        time = seconds + minutes * SECONDS_PER_OPTION['minutes'] + hours * SECONDS_PER_OPTION['hours'] + days * SECONDS_PER_OPTION['days'] + weeks * SECONDS_PER_OPTION['weeks']
        while True:
            time -= 1
            await asyncio.sleep(1)  # Check every second

            if time <= 0:
                return await ctx.channel.send(f"{ctx.user.mention} Your timer has ended!")


def setup(bot):
    bot.add_cog(Timers(bot))
