import logging
import asyncio
import discord
from discord.ext import commands
from helpers.embed_handler import success, failure
from helpers.misc import tail
from helpers.paginator import Paginator
from helpers.converters import license_duration
from helpers.licence_helper import construct_expiration_date

logger = logging.getLogger(__name__)
update_channel_id = 625404542535598090


class BotOwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, extension_path):
        """
        Loads an extension.
        :param extension_path: full path, dotted access.
        """
        self.bot.load_extension(extension_path)
        await ctx.send(embed=success(f"{extension_path} loaded.", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unload(self, ctx, extension_path):
        """
        Unloads an extension.
        :param extension_path: full path, dotted access
        """

        self.bot.unload_extension(extension_path)
        await ctx.send(embed=success(f"{extension_path} unloaded.", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def disconnect(self, ctx):
        """
        Closes database connection and disconnects the bot.

        Used for gracefully shutting it down in need of update.
        """
        await self.bot.main_db.connection.commit()
        await self.bot.main_db.connection.close()
        logger.info("Database closed.")
        await self.bot.logout()
        logger.info("Disconnected.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update(self, ctx):
        count_minutes = 15
        for i in range(count_minutes, 0, -1):
            await self.bot.change_presence(activity=discord.Game(name=f"Update in {i}"))
            await asyncio.sleep(60)

        progress_msg = ("```diff\n"
                        "- ----------------------\n"
                        "+   Update in progress\n"
                        "- ----------------------\n"
                        "```")
        update_channel = self.bot.get_channel(update_channel_id)
        await update_channel.send(progress_msg)
        await self.bot.change_presence(activity=discord.Game(name="Update in progress!"))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update_done(self, ctx):
        msg = ("```diff\n"
               "- -------------------------------------------------------------\n"
               "+   Update done. All changes above this message are now live!\n"
               "- -------------------------------------------------------------\n"
               "```")
        update_channel = self.bot.get_channel(update_channel_id)
        await update_channel.send(msg)
        await self.bot.change_presence(activity=discord.Game(name="Roles!"))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def playing(self, ctx, *, game):
        await self.bot.change_presence(activity=discord.Game(name=game))
        logger.info(f"Successfully set presence to **Playing {game}**.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def streaming(self, ctx, name, url):
        """
        Discord py currently only supports twitch urls.

        """
        if "//www.twitch.tv" not in url:
            await ctx.send(embed=failure("Only twitch urls supported!"))
            return
        await self.bot.change_presence(activity=discord.Streaming(name=name, url=url))
        logger.info(f"Successfully set presence to **Streaming {name}**.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def listening(self, ctx, *, song):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=song))
        logger.info(f"Successfully set presence to **Listening to {song}**.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def watching(self, ctx, *, movie):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=movie))
        logger.info(f"Successfully set presence to **Watching {movie}**.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_config(self, ctx):
        """
        Reloads json config.

        """
        self.bot.config.reload_config()
        msg = "Successfully reloaded config."
        logger.info(msg)
        await ctx.send(embed=success(msg, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def show_log(self, ctx, lines=100):
        """
        Shows last n lines from log.txt

        Max lines 10 000.
        Sends multiple messages at once if needed.
        """
        if lines > 10_000:
            lines = 10_000

        log = "".join(tail(lines))
        await Paginator.paginate(self.bot, ctx.author, ctx.author, log,
                                 title=f"Last {lines} log lines.\n\n", prefix="```DNS\n")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def valid(self, ctx, license):
        """
        Checks if passed license is valid

        """
        if await self.bot.main_db.is_valid_license(license, ctx.guild.id):
            await ctx.send(embed=success("License is valid", ctx.me))
        else:
            await ctx.send(embed=failure(f"License is not valid."))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def guilds_diagnostic(self, ctx):
        loaded_guilds = tuple(guild.id for guild in self.bot.guilds)
        db_guilds = await self.bot.main_db.get_all_guild_ids()
        difference = set(loaded_guilds).symmetric_difference(set(db_guilds))
        difference = None if len(difference) == 0 else difference
        message = (f"Loaded guilds: {len(loaded_guilds)}\n"
                   f"Database guilds: {len(db_guilds)}\n"
                   f"Difference: {difference}")
        await ctx.send(embed=success(message, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def guild_diagnostic(self, ctx, guild_id: int = None):
        """
        A shortened version of guild_info command without any checks and
        including additional data from the guild object.

        minus DRY :(
        """
        if guild_id is None:
            guild_id = ctx.guild.id

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            loaded_msg = "Guild ID not found in loaded guilds."
        else:
            loaded_msg = (f"Guild info:\n"
                          f"Name: **{guild.name}**\n"
                          f"Description: **{guild.description}**\n"
                          f"Owner ID: **{guild.owner_id}**\n"
                          f"Member count: **{guild.member_count}**\n"
                          f"Role count: **{len(guild.roles)}**\n"
                          f"Verification level: **{guild.verification_level}**\n"
                          f"Premium tier: **{guild.premium_tier}**\n"
                          f"System channel: **{guild.system_channel.id}**\n"
                          f"Region: **{guild.region}**\n"
                          f"Unavailable: **{guild.unavailable}**\n"
                          f"Created date: **{guild.created_at}**\n"
                          f"Features: **{guild.features}**"
                          )

        prefix, role_id, expiration = await self.bot.main_db.get_guild_info(guild_id)
        stored_license_count = await self.bot.main_db.get_guild_license_total_count(guild_id)
        active_license_count = await self.bot.main_db.get_guild_licensed_roles_total_count(guild_id)

        if role_id is None:
            role_id = "**Not set!**"

        db_msg = (f"Database guild info:\n"
                  f"Prefix: **{prefix}**\n"
                  f"Default license role: {role_id}\n"
                  f"Default license expiration time: **{expiration}h**\n"
                  f"Stored licenses: **{stored_license_count}**\n"
                  f"Active role subscriptions: **{active_license_count}**")

        await ctx.send(embed=success(f"{db_msg}\n\n{loaded_msg}", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_remove_all_guild_data(self, ctx, guild_id: int, guild_too: int = 0):
        """
        :param guild_id: guild in question
        :param guild_too: default 0. Pass 1 to delete guild table too.

        """
        await self.bot.main_db.remove_all_guild_data(guild_id, guild_too)
        await ctx.send(embed=success("Done", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_new_licensed_member(self, ctx, member: discord.Member, role: discord.Role,
                                        *, license_dur: license_duration):
        expiration_date = construct_expiration_date(license_dur)
        await self.bot.main_db.add_new_licensed_member(member.id, ctx.guild.id, expiration_date, role.id)
        await ctx.send(embed=success("Done", ctx.me))


def setup(bot):
    bot.add_cog(BotOwnerCommands(bot))
