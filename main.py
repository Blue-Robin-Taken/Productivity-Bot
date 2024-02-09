# --- Imports ---
import discord
import os


# --- Basic Setup ---
bot = discord.Bot()


# Cog loading
# https://docs.pycord.dev/en/stable/ext/commands/cogs.html

for filename in os.listdir('./cogs'):  # https://stackoverflow.com/a/77405177/15982771
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
        print(f"Loaded Cog: {filename[:-3]}")


# --- Events ---
@bot.event
async def on_ready():
    print('Bot is ready')


@bot.listen()  # Listen won't override bot.sync_commands
async def on_connect():
    print("Bot has connected")


# Run bot
bot.run(str(os.getenv('BOT_TOKEN')))
