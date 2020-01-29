import logging
import discord
from aiosqlite import IntegrityError
from discord.ext import commands
from helpers.embed_handler import success, failure
from helpers.converters import license_duration

logger = logging.getLogger(__name__)


class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.startup_guild_database_check())

    async def startup_guild_database_check(self):
        db_guilds_ids = await self.bot.main_db.get_all_guild_ids()
        logger.info("Starting database guild checkup..")
        await self.bot.wait_until_ready()
        # Checks for new guilds
        for guild in self.bot.guilds:
            if guild.id not in db_guilds_ids:
                logger.info(f"Guild {guild.id} {guild} found but not registered. "
                            f"Adding entry to database.")
                await self.bot.main_db.setup_new_guild(guild.id, self.bot.config["default_prefix"])

        # Do not code the other way around
        # aka deleting database data if the guild in database doesn't exist in bot guilds
        # Discord downtimes can cause bot to not see the guilds and they will reappear after downtime
        logger.info("Database guild checkup done!")

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def prefix(self, ctx, *, prefix):
        """
        Changes guild prefix.
        Maximum prefix size is 5 characters.

        """
        if ctx.prefix == prefix:
            await ctx.send(embed=failure(f"Already using prefix **{prefix}**"))
            return

        try:
            await self.bot.main_db.change_guild_prefix(ctx.guild.id, prefix)
        except IntegrityError:
            await ctx.send(embed=failure("Prefix is too long! Maximum of 5 characters please."))
            return

        await ctx.send(embed=success(f"Successfully changed prefix to **{prefix}**", ctx.me))

    @commands.command()
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def default_role(self, ctx, role: discord.Role):
        """
        Changes default guild license role.

        When creating new license, and role is not passed, this is the default role the license will use.
        Role tied to license is the role that the member will get when he redeems it.

        """
        # Check if the role is manageable by bot
        if not ctx.me.top_role > role:
            await ctx.send(embed=failure("I can only manage roles **below** me in hierarchy."))
            return
        await self.bot.main_db.change_default_guild_role(ctx.guild.id, role.id)
        await ctx.send(embed=success(f"{role.mention} set as default!", ctx.me))

    @commands.command(aliases=["license_expiration", "expiration"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def default_expiration(self, ctx, expiration: license_duration):
        """
        Sets default guild role expiration time.

        When creating new license, and expiration time is not passed, this is the default time the license will use.
        Newly created licenses will expire after this much time.

        License duration is either a number representing hours or a string consisting of words in format:
        each word has to contain [integer][type format], entries are separated by space.

        Formats are:
        years y months m weeks w days d hours h

        License duration examples:
        20
        2y 5months
        1m
        3d 12h
        1w 2m 1w
        1week 1week
        12hours 5d

        """
        await self.bot.main_db.change_default_license_expiration(ctx.guild.id, expiration)
        await ctx.send(embed=success(f"Default license expiration set to **{expiration}h**!", ctx.me))

    @commands.command()
    @commands.guild_only()
    async def guild_info(self, ctx):
        """
        Shows database data for the guild.

        """
        prefix, role_id, expiration = await self.bot.main_db.get_guild_info(ctx.guild.id)
        stored_license_count = await self.bot.main_db.get_guild_license_total_count(ctx.guild.id)
        active_license_count = await self.bot.main_db.get_guild_licensed_roles_total_count(ctx.guild.id)

        # If the bot just joined the guild it can happen that the default license role is not set.
        if role_id is not None:
            default_license_role = discord.utils.get(ctx.guild.roles, id=int(role_id))
            # In case it is set in db but was deleted from the guild.
            # This is needed in case the bot was offline and role was deleted
            # because on_guild_role_delete will not fire (we delete it from db in that event if that deleted role
            # is set as default guild role).
            # TODO: ABOVE EVENT
            if default_license_role is None:
                default_license_role = role_id
                log = f"Can't find default license role {role_id} from guild {ctx.guild.name},{ctx.guild.id}"
                msg = (f"Can't find default role {role_id} in this guild!\n"
                       f"It's saved in the database but it looks like it was deleted from the guild.\n"
                       f"Please update it.")
                logger.critical(log)
                await ctx.send(embed=failure(msg))
            else:
                default_license_role = default_license_role.mention
        else:
            default_license_role = "**Not set!**"

        msg = (f"Database guild info:\n"
               f"Prefix: **{prefix}**\n"
               f"Default license role: {default_license_role}\n"
               f"Default license expiration time: **{expiration}h**\n\n"
               f"Stored licenses: **{stored_license_count}**\n"
               f"Active role subscriptions: **{active_license_count}**")

        await ctx.send(embed=success(msg, ctx.me))


def setup(bot):
    bot.add_cog(Guild(bot))
