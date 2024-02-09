# --- This is the To-Do Cog for commands related to To-Do ---

import discord
from discord.ext import commands
import sqlite3


class ToDo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- SQL startup ---

    con = sqlite3.connect("todo.db")
    cur = con.cursor()
    try:
        cur.execute("CREATE TABLE lists(title, description, user_id)")
        print("Created new table for ToDo")
    except sqlite3.OperationalError:
        print("Found existing table for ToDo")

    to_do_group = discord.SlashCommandGroup("to-do")

    @to_do_group.command()
    async def create(self, ctx,
                     name: discord.Option(description="The name for your to-do list.", required=True, min_length=1,
                                          max_length=10),
                     description: discord.Option(description="The description for your to-do list", required=False)):
        if not description:  # if description is empty
            description = "No description provided."

        # -- If there is already a title with that same name and user --
        ref = self.cur.execute(f"""SELECT * FROM lists
        WHERE title = '{name}' AND user_id={ctx.user.id};""")
        fetch_one = ref.fetchone()

        if fetch_one:
            return await ctx.respond("You already have a to-do list of this name. Please delete that first before creating one of the same name.")

        # -- Creating the new list --
        self.cur.execute(f"""INSERT INTO lists 
        VALUES ('{name}', '{description}', {ctx.user.id});""")
        self.con.commit()  # save changes
        await ctx.respond(f"Created the list `{name}`!")
    


def setup(bot):
    bot.add_cog(ToDo(bot))
