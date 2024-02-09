# --- Imports ---
import discord
import os

# --- Basic Setup ---
bot = discord.Bot()


# Cog loading


# --- Events ---
@bot.event
async def on_ready():
    print('Bot is ready')


@bot.listen()  # Listen won't override bot.sync_commands
async def on_connect():
    print("Bot has connected")


# Run bot
bot.run(str(os.getenv('BOT_TOKEN')))
