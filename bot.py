import discord
from discord.ext import commands
from database_handler import DatabaseHandler
from config_handler import ConfigHandler
import sys

startup_extensions = ["licenses", "database_debug", "bot_presence", "cmd_errors"]
bot = commands.Bot(command_prefix="!")

# Load and set loaded config as botvar
bot.config = ConfigHandler()

if __name__ == "__main__":
    print("Loaded extensions:")
    for extension in startup_extensions:
        cog_path = f"cogs.{extension}"
        try:
            bot.load_extension(cog_path)
            print(f"\t{cog_path}")
        except Exception as e:
            exc = f"{type(e).__name__}: {e}"
            print(f"{exc} Failed to load extension {cog_path}")


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


@bot.event
async def on_error(event: str, *args, **kwargs):
    """
    Called when an EVENT raises an uncaught exception

    This doesn't use the same event system as the rest of events despite being documented as such
    Can only have one and it's gotta be in main file.
    """
    exc_info = sys.exc_info()
    exc_type = exc_info[0].__name__ if exc_info[0] is not None else "<no exception>"
    exc_what = str(exc_info[1]) if exc_info[1] is not None else ""
    print(f"Uncaught {exc_type} in '{event}': {exc_what}")


bot.run(bot.config.get_token())
