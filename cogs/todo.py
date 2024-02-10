# --- This is the To-Do Cog for commands related to To-Do ---

import discord
from discord.ext import commands
import sqlite3
from discord.ui import View, Button, Modal, InputText
from discord import InputTextStyle


# --- Item Related Classes ---
class AddItemButton(Button):
    def __init__(self, ):
        super().__init__(style=discord.ButtonStyle.blurple, label="Add Item", emoji="➕")

    async def callback(self, interaction):

        await interaction.response.send_modal(AddItemModal())


class ToDoListButtonsUI(View):
    def __init__(self, ):
        super().__init__()
        self.add_item(AddItemButton())


class AddItemModal(Modal):  # https://guide.pycord.dev/interactions/ui-components/modal-dialogs
    def __init__(self):
        super().__init__(InputText(style=InputTextStyle.short, label="title", placeholder="Input a title here"),
                         title="Add an item to the to-do list")

    async def callback(self, interaction):
        await interaction.response.send_message("Added item")


# --- Main Cog ---
class ToDo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- SQL startup ---

    con = sqlite3.connect("todo.db")
    cur = con.cursor()
    try:
        cur.execute("CREATE TABLE tablesList(title, description, user_id)")
        print("Created new tablesList table for ToDo")
    except sqlite3.OperationalError:
        print("Found existing table for ToDo")
    try:
        cur.execute("CREATE TABLE todoListItems(title, user_id, item_name, item_description)")
        print("Created new todoListItems table for ToDo")
    except sqlite3.OperationalError:
        print("Found existing table for ToDo")

    # --- Static commands ---

    async def getTableEmbed(self, title, user_id: int):
        ref = self.cur.execute(f"""SELECT * FROM todoListItems WHERE title='{title}' AND user_id={user_id}""")
        ref_fetch = ref.fetchall()

        return_embed = discord.Embed(title=title)
        if ref_fetch:
            for item in ref_fetch:
                return_embed.add_field(name=item[0], value=item[1])

        return return_embed

    # --- Slash Commands ---

    to_do_group = discord.SlashCommandGroup("to-do")

    @to_do_group.command()
    async def create(self, ctx,
                     name: discord.Option(description="The name for your to-do list.", required=True, min_length=1,
                                          max_length=10),
                     description: discord.Option(description="The description for your to-do list", required=False)):
        if not description:  # if description is empty
            description = "No description provided."

        # -- If there is already a title with that same name and user --
        ref = self.cur.execute(f"""SELECT * FROM tablesList
        WHERE title = '{name}' AND user_id={ctx.user.id};""")
        fetch_one = ref.fetchone()

        if fetch_one:
            return await ctx.respond(
                "You already have a to-do list of this name. Please delete that first before creating one of the same name.")

        # -- Creating the new list --
        self.cur.execute(f"""INSERT INTO tablesList 
        VALUES ('{name}', '{description}', {ctx.user.id});""")
        self.con.commit()  # save changes

        # -- Create responses --
        await ctx.respond(f"Created the list `{name}`!")
        await ctx.channel.send(embed=await self.getTableEmbed(name, ctx.user.id), view=ToDoListButtonsUI())


def setup(bot):
    bot.add_cog(ToDo(bot))
