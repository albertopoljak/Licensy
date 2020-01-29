import traceback
import logging
import asyncio
import sys
from datetime import datetime
import discord
from discord.ext import commands
from database_handler import DatabaseHandler
from config_handler import ConfigHandler
from helpers import logger_handlers, embed_handler
from helpers.embed_handler import success
from helpers.licence_helper import get_current_time

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(logger_handlers.get_console_handler())
root_logger.addHandler(logger_handlers.get_file_handler())
logger = logging.getLogger("discord")
logger.setLevel(logging.WARNING)

config_handler = ConfigHandler("config")
database_handler = asyncio.get_event_loop().run_until_complete(DatabaseHandler.create())

startup_extensions = ["licenses",
                      "bot_owner_commands",
                      "guild",
                      "bot_information",
                      "help",
                      "top_gg_api",
                      "cmd_errors"]


async def prefix_callable(bot_client, message):
    try: 
        # TODO: Store this in list or something so we don't waste calls to db for each message
        # TODO: although it's pretty fast (instant)
        return await bot_client.main_db.get_guild_prefix(message.guild.id)
    except Exception as err:
        """
        If fetching prefix from database errors just use the default prefix.
        This is also used in DMs where the guild is None
        """
        default_prefix = config_handler["default_prefix"]
        if message.guild is not None:
            # Don't spam the log if it's DMs
            # We only want to log it in case guild prefix is missing
            root_logger.error(f"Can't get guild {message.guild} prefix. Error:{err}. "
                              f"Using '{default_prefix}' as prefix.")
        return default_prefix


bot = commands.Bot(command_prefix=prefix_callable, description=config_handler["bot_description"], case_insensitive=True)
bot.config = config_handler
bot.main_db = database_handler
bot.up_time_start_time = get_current_time()

if __name__ == "__main__":
    root_logger.info("Loaded extensions:")
    for extension in startup_extensions:
        cog_path = f"cogs.{extension}"
        try:
            bot.load_extension(cog_path)
            root_logger.info(f"{cog_path}")
        except Exception as e:
            exc = f"{type(e).__name__}: {e}"
            root_logger.error(f"{exc} Failed to load extension {cog_path}")
            traceback_msg = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            root_logger.warning(traceback_msg)


@commands.is_owner()
@bot.command(hidden=True)
async def load(ctx, extension_path):
    """
    Loads an extension.
    :param extension_path: full path, dotted access

    """
    bot.load_extension(extension_path)
    await ctx.send(embed=success(f"{extension_path} loaded.", ctx.me))


@commands.is_owner()
@bot.command(hidden=True)
async def unload(ctx, extension_path):
    """
    Unloads an extension.
    :param extension_path: full path, dotted access

    """
    bot.unload_extension(extension_path)
    await ctx.send(embed=success(f"{extension_path} unloaded.", ctx.me))


@commands.is_owner()
@bot.command(hidden=True)
async def disconnect(ctx):
    """
    Closes database connection and disconnects the bot.

    Used for gracefully shutting it down in need of update.

    """
    await bot.main_db.connection.commit()
    await bot.main_db.connection.close()
    root_logger.info("Database closed.")
    await bot.logout()
    root_logger.info("Disconnected.")


@bot.event
async def on_connect():
    root_logger.info("Connection to Discord established")


@bot.event
async def on_guild_remove(guild):
    root_logger.info(f"Left guild {guild.name}")


@bot.event
async def on_disconnect():
    root_logger.warning("Connection lost")


@bot.event
async def on_ready():
    root_logger.info(f"Logged in as: {bot.user.name} - {bot.user.id}"
                     f"\tDiscordPy version: {discord.__version__}")
    root_logger.info("Successfully logged in and booted...!")


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
    log_message = f"Uncaught {exc_type} in '{event}': {exc_what}"
    traceback_message = traceback.format_exc()
    root_logger.critical(log_message)
    root_logger.critical(traceback_message)
    if bot.is_ready():
        log_channel = bot.get_channel(config_handler["developer_log_channel_id"])
        embed = embed_handler.log_embed(log_message, title="on_error exception!")
        embed_traceback = embed_handler.traceback_embed(traceback_message)
        if log_channel is not None:
            await log_channel.send(embed=embed)
            await log_channel.send(embed=embed_traceback)


bot.run(bot.config["token"])
