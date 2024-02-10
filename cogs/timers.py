import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, InputText
from discord import InputTextStyle

import sqlite3
import asyncio
import os


def embed_create(title, description, color, field_name=None, field_value=None):
    if field_name is None:
        em = discord.Embed(title=title, description=description, color=color)

        return em
    else:
        em = discord.Embed(title=title, description=description, color=color)
        em.add_field(name=field_name, value=field_value)

        return em


class Timers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print('Timer Loaded')

    timer_group = discord.SlashCommandGroup('timer')

    @timer_group.command()
    async def create(self, ctx, *,
                     length: discord.Option(description="The length of the timer", required=True,
                                            min_length=1)):
        if "s" in length:
            a = length.split("s")[0]
            em = embed_create(title="Timer",
                              description=f"Your timer of {a} second(s) has been created.",
                              color=ctx.author.color)
            await ctx.respond(embed=em)
            await asyncio.sleep(int(a))
            em = embed_create(title="Timer",
                              description=f"{ctx.author.mention}, your timer is finished!",
                              color=ctx.author.color)
            await ctx.respond(embed=em)
        elif "m" in length:
            a = length.split("m")[0]
            em = embed_create(title="Timer",
                              description=f"Your timer of {a} minute(s) has been created.",
                              color=ctx.author.color)
            await ctx.respond(embed=em)
            await asyncio.sleep(int(a) * 60)
            em = embed_create(title="Timer",
                              description=f"{ctx.author.mention}, your timer is finished!",
                              color=ctx.author.color)
            await ctx.respond(embed=em)
        elif "h" in length:
            a = length.split("h")[0]
            em = embed_create(title="Timer",
                              description=f"Your timer of {a} hour(s) has been created.",
                              color=ctx.author.color)
            await ctx.respond(embed=em)
            await asyncio.sleep(int(a) * 3600)
            em = embed_create(title="Timer",
                              description=f"{ctx.author.mention}, your timer is finished!",
                              color=ctx.author.color)
            await ctx.respond(embed=em)
        else:
            em = embed_create(title="Invalid Timer",
                              description=f"Invalid Parameters. Try 1s, 1m, 1h",
                              color=ctx.author.color)
            await ctx.respond(embed=em)


def setup(bot):
    bot.add_cog(Timers(bot))
