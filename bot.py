import discord
from discord.ext import commands
from database_handler import DatabaseHandler
import traceback

startup_extensions = ["cogs.licenses", "cogs.db_test", "cogs.cmd_errors"]
bot = commands.Bot(command_prefix="!")

if __name__ == "__main__":
    print("Loaded extensions:")
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
            print(f"\t{extension}")
        except Exception as e:
            exc = f"{type(e).__name__}: {e}"
            print(f"{exc} Failed to load extension {extension}")
            traceback.print_exc()


@bot.event
async def on_connect():
    print("\nConnection to Discord established")
    try:
        bot.main_db
    except AttributeError:
        print("Creating new db connection")
        bot.main_db = await DatabaseHandler.create()


@bot.event
async def on_guild_remove(guild):
    print(f"Left guild {guild.name}")


@bot.event
async def on_disconnect():
    print("Connection lost")


@bot.event
async def on_ready():
    print(f"\nLogged in as: {bot.user.name} - {bot.user.id}"
          f"\nDiscordPy version: {discord.__version__}\n")
    print("Successfully logged in and booted...!\n")


bot.run()
