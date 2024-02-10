# --- This is the To-Do Cog for commands related to To-Do ---

import discord
from discord.ext import commands
import sqlite3
from discord.ui import View, Button, Modal, InputText
from discord import InputTextStyle

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
    # Order: title of the database, user's id, the item's name, the item's description
    print("Created new todoListItems table for ToDo")
except sqlite3.OperationalError:
    print("Found existing table for ToDo")


# --- Non Class Static Funcs ---
async def getAllToDoLists(ctx):
    ref = cur.execute(f"""SELECT * FROM tablesList WHERE user_id={ctx.interaction.user.id}""")
    ref_fetch = ref.fetchall()
    options_list = [discord.OptionChoice(name=item[0]) for item in ref_fetch]
    return_list = []
    if ctx.value:
        # -- Narrowing down search options by checking if it's a subset --

        for item in options_list:
            if all(elem in list(item.name.lower()) for elem in list(ctx.value.lower())):  # https://stackoverflow.com/questions/3931541/how-to-check-if-all-of-the-following-items-are-in-a-list
                return_list.append(item.name)

        return return_list
    return options_list


# --- Item Related Classes ---
class AddItemButton(Button):
    def __init__(self, title):
        super().__init__(style=discord.ButtonStyle.blurple, label="Add Item", emoji="➕")
        self.title = title

    async def callback(self, interaction):
        await interaction.response.send_modal(AddItemModal(message=self.view.message, title=self.title))


class ToDoListButtonsUI(View):
    def __init__(self, title):
        super().__init__(timeout=600, disable_on_timeout=True)  # timeout is in seconds, so 600 = 10 minutes
        self.add_item(AddItemButton(title=title))


class AddItemModal(Modal):  # https://guide.pycord.dev/interactions/ui-components/modal-dialogs
    def __init__(self, message, title):
        super().__init__(InputText(style=InputTextStyle.short, label="title", placeholder="Input a title here"),
                         InputText(style=InputTextStyle.long, label="description",
                                   placeholder="Input a description here"),
                         title="Add an item to the to-do list", )
        self.message = message  # message to edit after new cards/things were added
        self.title = title  # the title of the specific to-do list to link back to the user

    async def callback(self, interaction):
        print([i.value for i in self.children])
        cur.execute(f"""INSERT INTO todoListItems
        VALUES (?, ?, ?, ?);""", (self.title, interaction.user.id, self.children[0].value, self.children[1].value))
        #  https://stackoverflow.com/questions/45575608/python-sqlite-operationalerror-near-s-syntax-error
        con.commit()  # save changes

        # --- Feedback to user ---
        await self.message.edit(embed=await ToDo.getTableEmbed(title=self.title, user_id=interaction.user.id))
        await interaction.response.send_message("Added item")


# --- Main Cog ---
class ToDo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Static commands ---

    @staticmethod
    async def getTableEmbed(title, user_id: int):
        ref = cur.execute(f"""SELECT * FROM todoListItems WHERE title='{title}' AND user_id={user_id}""")
        ref_fetch = ref.fetchall()

        return_embed = discord.Embed(title=title, color=discord.Color.random())
        print(ref_fetch)
        if ref_fetch:
            for item in ref_fetch:
                return_embed.add_field(name=item[2], value=item[3], inline=False)

        return return_embed

    # --- Slash Commands ---

    to_do_group = discord.SlashCommandGroup("to-do")

    @to_do_group.command()
    async def create(self, ctx,
                     name: discord.Option(description="The name for your to-do list.", required=True, min_length=1,
                                          max_length=25),
                     description: discord.Option(description="The description for your to-do list", required=False)):
        if not description:  # if description is empty
            description = "No description provided."

        # -- If there is already a title with that same name and user --
        ref = cur.execute(f"""SELECT * FROM tablesList
        WHERE title = '{name}' AND user_id={ctx.user.id};""")
        fetch_one = ref.fetchone()

        if fetch_one:
            return await ctx.respond(
                "You already have a to-do list of this name. Please delete that first before creating one of the same name.")

        # -- Creating the new list --
        cur.execute(f"""INSERT INTO tablesList 
        VALUES ('{name}', '{description}', {ctx.user.id});""")
        con.commit()  # save changes

        # -- Create responses --
        await ctx.respond(f"Created the list `{name}`!")
        await ctx.channel.send(embed=await self.getTableEmbed(name, ctx.user.id), view=ToDoListButtonsUI(title=name))

    @to_do_group.command()
    async def get(self, ctx,
                  name: discord.Option(str, autocomplete=getAllToDoLists,
                                       description="The name for your to-do list.")):
        await ctx.respond(embed=await self.getTableEmbed(title=name, user_id=ctx.user.id),
                          view=ToDoListButtonsUI(title=name))

    @to_do_group.command()
    async def delete_all_lists(self, ctx):
        button = Button(style=discord.ButtonStyle.danger, label="Yes", emoji="❌")

        async def button_callback(interaction):
            interaction.response.send_message("Deleting all of your to-do lists.")

        button.callback = button_callback

        class ConfirmView(View):
            def __init__(self):
                super().__init__()
                self.add_item(button)

        await ctx.respond(embed=discord.Embed(title="Are you sure you want to do this?"), view=ConfirmView)


def setup(bot):
    bot.add_cog(ToDo(bot))
