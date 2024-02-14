# --- This is the To-Do Cog for commands related to To-Do ---

import discord
from discord.ext import commands
import sqlite3
from discord.ui import View, Button, Modal, InputText, Select
from discord import InputTextStyle, SelectOption
import time

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

async def getTableEmbed(title, user_id: int):
    ref = cur.execute(f"""SELECT * FROM tablesList WHERE title='{title}' AND user_id={user_id}""")
    description = ref.fetchone()[1]

    return_embed = discord.Embed(title=title, description=description, color=discord.Color.random())
    ref = cur.execute(f"""SELECT * FROM todoListItems WHERE title='{title}' AND user_id={user_id}""")
    ref_fetch = ref.fetchall()
    if ref_fetch:
        for item in ref_fetch:
            return_embed.add_field(name=item[2], value=item[3], inline=False)

    return return_embed


async def getAllToDoLists(ctx):
    ref = cur.execute(f"""SELECT * FROM tablesList WHERE user_id={ctx.interaction.user.id}""")
    ref_fetch = ref.fetchall()
    options_list = [discord.OptionChoice(name=item[0]) for item in ref_fetch]
    return_list = []
    if ctx.value:
        # -- Narrowing down search options by checking if it's a subset --

        for item in options_list:
            if all(elem in list(item.name.lower()) for elem in
                   list(
                       ctx.value.lower())):  # https://stackoverflow.com/questions/3931541/how-to-check-if-all-of-the-following-items-are-in-a-list
                return_list.append(item.name)

        return return_list
    return options_list


def shortenLength(input_string: str, length: int):
    if len(input_string) > length:
        return str(input_string[0:length])
    return str(input_string)


async def checkTitle(title: str, user_id: int):
    """
    This function checks the title of an input and checks if it's in the database with that user.
    """
    title = title.strip()
    ref = cur.execute(f"""SELECT * FROM tablesList
    WHERE title = '{title}' AND user_id={user_id};""")
    fetch_one = ref.fetchone()

    return fetch_one  # Will return either None or the fetch if it exists


def itemsExistInList(title: str, user_id: int):
    """
    Checks if there are items under a to-do list
    """
    ref = cur.execute(f"""SELECT * FROM todoListItems
    WHERE title = '{title}' AND user_id={user_id};""")
    fetch_one = ref.fetchall()

    return fetch_one  # Will return either None or the fetch if it exists


async def checkItem(item_name: str, user_id: int):
    """
    This function checks the item name with the user's id in the items database to see if it exists.
    If it does exist it returns that row. Else, it returns None.
    """

    item_name = item_name.strip()
    ref = cur.execute(f"""SELECT * FROM todoListItems
    WHERE title = '{item_name}' AND user_id={user_id};""")
    fetch_one = ref.fetchone()

    return fetch_one  # Will return either None or the fetch if it exists


# --- Item Related Classes ---
class AddItemButton(Button):
    def __init__(self, title):
        super().__init__(style=discord.ButtonStyle.blurple, label="Add Item", emoji="➕")
        self.title = title

    async def callback(self, interaction):
        await interaction.response.send_modal(AddItemModal(message=self.view.message, title=self.title))

        await self.view.message.edit(view=self.view)


class RemoveItemButton(Button):
    """
    This class is for prompting the remove select menu
    """
    def __init__(self, title):
        super().__init__(emoji="✖", style=discord.ButtonStyle.danger, label="Remove")
        self.title = title

    async def callback(self, interaction):
        fetch_one = itemsExistInList(title=self.title, user_id=interaction.user.id)

        if not fetch_one:
            return await interaction.response.send_message("You don't have any items in this to-do list!", ephemeral=True)

        # -- Create response for correct input --
        embed = discord.Embed(
            title="What items do you want to remove?",
            description="Select one or more items to remove from your to-do list.",
            color=discord.Color.dark_red()
        )

        view = View()
        view.add_item(ItemDeleteSelect(user_id=interaction.user.id, title=self.title))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ToDoListButtonsUI(View):
    def __init__(self, title):
        super().__init__(timeout=600, disable_on_timeout=True)  # timeout is in seconds, so 600 = 10 minutes
        self.add_item(AddItemButton(title=title))
        self.add_item(RemoveItemButton(title=title))


class ItemDeleteSelect(Select):
    def __init__(self, user_id, title):
        # -- Generate options --
        options_ref = cur.execute(f"SELECT * FROM todoListItems WHERE title='{title}' AND user_id={user_id}")
        fetch_all = options_ref.fetchall()
        options = [SelectOption(label=shortenLength(option[2], 100), description=shortenLength(option[3], 100)) for
                   option in fetch_all]

        # -- Calculate the max amount of select so that there's at most 25 or the length of the options --
        max_amount = 25
        if len(options) < 25:
            max_amount = len(options)

        # -- Set super --
        super().__init__(options=options, min_values=1, max_values=max_amount, custom_id="delete")

        # -- Self vars --
        self.title = title
        self.user_id = user_id

    async def callback(self, interaction):
        await interaction.response.defer()
        for value in self.values:
            cur.execute(f"DELETE FROM todoListItems WHERE item_name=? AND user_id=?", (str(value), interaction.user.id))
        con.commit()
        deletions = "\n".join(self.values)
        embed = discord.Embed(
            title="Deletion successful!",
            description=f"Deleted the following: {deletions}",
            color=discord.Color.green()
        )
        # -- Create response --

        # Disable view
        self.view.disable_all_items()
        await self.view.message.edit(view=self.view)
        await interaction.followup.send(embed=embed, ephemeral=True)


class AddItemModal(Modal):  # https://guide.pycord.dev/interactions/ui-components/modal-dialogs
    def __init__(self, message, title):
        super().__init__(
            InputText(style=InputTextStyle.short, label="title", placeholder="Input a title here", max_length=100),
            InputText(style=InputTextStyle.long, label="description",
                      placeholder="Input a description here", max_length=1024, min_length=1),
            title="Add an item to the to-do list", )
        self.message = message  # message to edit after new cards/things were added
        self.title = title  # the title of the specific to-do list to link back to the user

    async def callback(self, interaction):
        # -- Check if input is valid and does not exist already --
        fetch_one = await checkItem(item_name=self.children[0].value, user_id=interaction.user.id)

        if fetch_one:
            return await interaction.response.send_message("You already have an item with that name!", ephemeral=True)

        cur.execute(f"""INSERT INTO todoListItems
        VALUES (?, ?, ?, ?);""", (self.title, interaction.user.id, self.children[0].value, self.children[1].value))
        #  https://stackoverflow.com/questions/45575608/python-sqlite-operationalerror-near-s-syntax-error
        con.commit()  # save changes

        # --- Feedback to user ---
        await self.message.edit(embed=await getTableEmbed(title=self.title, user_id=interaction.user.id))
        await interaction.response.send_message(f"Added item `{self.children[0].value}`", ephemeral=True)


# --- Main Cog ---
class ToDo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        fetch_one = await checkTitle(title=name, user_id=ctx.user.id)

        if fetch_one:
            return await ctx.respond(
                "You already have a to-do list of this name. Please delete that first before creating one of the same name.")

        # -- Creating the new list --
        cur.execute(f"""INSERT INTO tablesList 
        VALUES ('{name}', '{description}', {ctx.user.id});""")
        con.commit()  # save changes

        # -- Create responses --
        await ctx.respond(f"Created the list `{name}`!")
        await ctx.channel.send(embed=await getTableEmbed(name, ctx.user.id),
                               view=ToDoListButtonsUI(title=name))

    @to_do_group.command()
    async def get(self, ctx,
                  name: discord.Option(str, autocomplete=getAllToDoLists,
                                       description="The name for your to-do list.")):
        await ctx.respond(embed=await getTableEmbed(title=name, user_id=ctx.user.id),
                          view=ToDoListButtonsUI(title=name))

    remove_subgroup = to_do_group.create_subgroup(name="remove")

    @remove_subgroup.command()
    async def item(self, ctx,
                   name: discord.Option(str, autocomplete=getAllToDoLists,
                                        description="The name for your to-do list.")):
        # -- Check for improper inputs --
        fetch_one = await checkTitle(title=name, user_id=ctx.user.id)

        if not fetch_one:
            return await ctx.respond("That to-do list does not exist!", ephemeral=True)

        fetch_one = itemsExistInList(title=name, user_id=ctx.user.id)

        if not fetch_one:
            return await ctx.respond("You don't have any items in this to-do list!", ephemeral=True)

        # -- Create response for correct input --
        embed = discord.Embed(
            title="What items do you want to remove?",
            description="Select one or more items to remove from your to-do list.",
            color=discord.Color.dark_red()
        )

        view = View()
        view.add_item(ItemDeleteSelect(user_id=ctx.user.id, title=name))
        await ctx.respond(embed=embed, view=view)

    @remove_subgroup.command()
    async def delete_all_lists(self, ctx):
        button = Button(style=discord.ButtonStyle.danger, label="Yes", emoji="🚮")
        view = View(disable_on_timeout=True, timeout=60)
        view.add_item(button)

        async def button_callback(interaction):
            await interaction.response.defer()
            view.disable_all_items()
            await interaction.edit_original_response(view=view)
            start_time = time.time()  # Use this to calculate the time it took later

            ref = cur.execute(
                f"SELECT * FROM tablesList WHERE user_id={interaction.user.id}")
            listsToBeDeleted = ref.fetchall()
            listsToBeDeletedText = ''.join(i[0] + '\n' for i in listsToBeDeleted)

            # -- First response --
            unfinished_embed = discord.Embed(
                title="Deleting... 💭",
                description=f"Deleting the following: \n {listsToBeDeletedText}",
                color=discord.Color.yellow()
            )
            followup_response = await interaction.followup.send(embed=unfinished_embed, ephemeral=True)

            # -- Deleting from the database
            cur.execute(
                f"DELETE FROM tablesList WHERE user_id={interaction.user.id}")  # delete from to-do list database
            cur.execute(
                f"DELETE FROM todoListItems WHERE user_id={interaction.user.id}")  # delete from the items for those to-dos
            con.commit()

            finished_embed = discord.Embed(
                title="Done deleting! ✔",
                description=f"Deleted the following: \n {listsToBeDeletedText}",
                color=discord.Color.green()
            )

            # -- Calculate the time it took --
            end_time = time.time() - start_time

            finished_embed.add_field(name="Took the following time:", value=str(end_time * 1000) + " Milliseconds")

            await followup_response.edit(embed=finished_embed)

        button.callback = button_callback

        await ctx.respond(embed=discord.Embed(title="Are you sure you want to do this?", color=discord.Color.red()),
                          view=view, ephemeral=True)


# --- Other Cog Setup ---
def setup(bot):
    bot.add_cog(ToDo(bot))
