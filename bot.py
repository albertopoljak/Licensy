import asyncio
import discord
from discord.ext import commands
from database_handler import DatabaseHandler
from config_handler import ConfigHandler
import sys

config_handler = ConfigHandler()
database_handler = asyncio.get_event_loop().run_until_complete(DatabaseHandler.create())

startup_extensions = ["licenses",
                      "database_debug",
                      "bot_presence",
                      "guild_admin"
                      "cmd_errors"]


def prefix_callable(bot_client, message):
    try:
        # TODO: Store this in list or smth so we don't waste calls to db for each message
        return bot_client.main_db.get_guild_prefix(message.guild.id)
    except Exception:
        return config_handler.get_default_prefix()


bot = commands.Bot(command_prefix=prefix_callable, description=config_handler.get_description())
# Set botvars
bot.config = config_handler
bot.main_db = database_handler

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
