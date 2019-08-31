import asyncio
import logging
from datetime import datetime
from dateutil import parser
import texttable
from discord.ext import commands
from discord.errors import Forbidden
import discord.utils
from aiosqlite import IntegrityError
from helpers import misc
from helpers.converters import positive_integer, license_duration
from helpers.errors import RoleNotFound, DatabaseMissingData
from helpers.licence_helper import construct_expiration_date, get_remaining_time

logger = logging.getLogger(__name__)


class LicenseHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.license_check_loop())

    async def license_check_loop(self):
        while True:
            # Wait until the event is set.
            # (if the event is set, return True immediately, otherwise block until task calls set())
            # wait_until_ready is set only once, when bot internal cache is loaded.
            # Need to wait because on startup if license is expired functions here will try
            # to get guild/member/role objects before the bot is even loaded thus resulting in exception.
            await self.bot.wait_until_ready()
            # Do not stop license check loop just because of error
            # Error can happen in rare cases, for example if the guild from db is not found
            # in loaded guilds of the bot.
            try:
                await self.check_all_active_licenses()
            except Exception as e:
                logger.critical(e)
                pass
            logger.info("License check done.")
            # Sleep 15 minutes
            await asyncio.sleep(900)

    async def check_all_active_licenses(self):
        """
        Checks all active member licenses in database and if license is expired then remove
        the role from member and send some message.

        TODO: In rare case, when the bot is offline for whatever reason (outage, lag etc) and
        TODO: if in that time window the bot is kicked out of guild then we will get exceptions
        TODO: when removing roles from members because those members are still in database
        TODO: but the bot cannot access them because it was kicked (usually we handle that in
        TODO: on_guild_remove event). So TODO add check if all guilds are available, if not
        TODO: then remove everything from database associated with it.

        TODO: Move query to database handler

        """
        async with self.bot.main_db.connection.execute("SELECT * FROM LICENSED_MEMBERS") as cursor:
            async for row in cursor:
                member_id = int(row[0])
                member_guild_id = int(row[1])
                expiration_date = parser.parse(row[2])
                licensed_role_id = int(row[3])
                if await LicenseHandler.has_license_expired(expiration_date):
                    logger.info(f"Expired license for member:{member_id} role:{licensed_role_id} guild:{member_guild_id}")
                    await self.remove_role(member_id, member_guild_id, licensed_role_id)
                    await self.bot.main_db.delete_licensed_member(member_id, licensed_role_id)
                    logger.info(f"Role {licensed_role_id} successfully removed from member:{member_id}")

    @staticmethod
    async def has_license_expired(expiration_date: datetime) -> bool:
        """
        Check if param expiration date is in past related to the current date.
        If it is in past then license is considered expired.
        :param expiration_date: datetime object
        :return: True if license is expired, False otherwise

        """
        if expiration_date < datetime.now():
            # Expired
            return True
        else:
            return False

    async def remove_role(self, member_id, guild_id, licensed_role_id):
        """
        Removes the specified role from member based on @params

        :param member_id: unique member id
        :param guild_id: guild ID from where the member is from. Needed because member can be in
                         multiple guilds at the same time.
        :param licensed_role_id: ID of a role to remove from member
        :raise discord.NotFound: If @licensed_role_id is not found for @member_id when removing the role

        """
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            raise Exception(f"Fatal exception. "
                            f"Guild **{guild_id}** loaded from database cannot be found in bot guilds!")

        member = guild.get_member(member_id)

        # If member has left the guild just return
        if member is None:
            logger.warning(f"Can't remove licensed role {licensed_role_id} from member {member_id} "
                           f"because he has left the guild {licensed_role_id} ({guild.name}).")
            return

        member_role = discord.utils.get(member.roles, id=licensed_role_id)
        if member_role is None:
            raise RoleNotFound(f"Can't remove licensed role {member_role} for {member.mention}."
                               f"Role not found ")
        else:
            await member.remove_roles(member_role)
            try:
                await member.send(f"Your license in guild **{guild}** has expired "
                                  f"for the following role: **{member_role}** ")
            except Forbidden:
                # Ignore if user has blocked DM
                pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logger.info(f"Guild {guild.name} {guild.id} joined.")
        guild_id = guild.id
        default_prefix = self.bot.config.get_default_prefix()
        await self.bot.main_db.setup_new_guild(guild_id, default_prefix)
        logger.info(f"Guild {guild.name} {guild.id} database data added.")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        # TODO sensitive information removal
        # TODO to be sure add some sleep before deleting
        guild_id = guild.id
        logger.info(f"Guild {guild.name} {guild.id} was removed. Removing all database entries.")
        await self.bot.main_db.remove_all_guild_data(guild_id)
        logger.info(f"Guild {guild.name} {guild.id} all database entries successfully removed.")

    @commands.command(aliases=["activate"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    async def redeem(self, ctx, license):
        """
        Adds role to member who invoked the command.

        If license is valid get the role linked to it and assign the role to the member who invoked the command.

        Removes license from the database (it was redeemed).

        TODO: Better security (right now license is visible in plain sight in guild)
        """
        await self.activate_license(ctx, license, ctx.author)

    @commands.command(allieses=["add_license"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def add_license(self, ctx, license, member: discord.Member):
        """
        Manually add license to member

        """
        await self.activate_license(ctx, license, member)

    async def activate_license(self, ctx, license, member):
        """
        :param ctx: invoked context
        :param license: license to add
        :param member: who to give role to
        """
        guild = ctx.guild
        if await self.bot.main_db.is_valid_license(license, guild.id):
            # Adding role to the member requires that role object
            # First we get the role linked to the license
            role_id = await self.bot.main_db.get_license_role_id(license)
            role = ctx.guild.get_role(role_id)
            # Now before doing anything check if member already has the role
            # Beside for logic (why redeem already existing subscription?) if we don't check this we will get
            # sqlite3.IntegrityError:
            #   UNIQUE constraint failed:LICENSED_MEMBERS.MEMBER_ID,LICENSED_MEMBERS.LICENSED_ROLE_ID
            # when adding new licensed member to table LICENSED_MEMBERS if member already has the role (because in that
            # table the member id and role id is unique aka can only have uniques roles tied to member id)
            if role in member.roles:
                # We notify user that he already has the role, we also show him the expiration date
                try:
                    expiration_date = await self.bot.main_db.get_member_license_expiration_date(member.id, role_id)
                except DatabaseMissingData as e:
                    msg = e.message
                    msg += "\nThe bot did not register you in the database with that role but somehow you have it." \
                           "\nThis probably means that you were manually assigned this role " \
                           "without using the bot license system." \
                           "\nHave someone remove the role from you and call this command again."
                    await ctx.send(msg)
                    return

                remaining_time = get_remaining_time(expiration_date)
                await ctx.send(f"{member.mention} you already have an active subscription for the {role.mention} role!"
                               f"\nIt's valid for another {remaining_time}")
                return
            # We add the role to the member, we do this before adding/removing stuff from db
            # just in case the bot doesn't have perms and throws exception (we already
            # checked for bot_has_permissions(manage_roles=True) but it can happen that bot has
            # that permission and check is passed but it's still forbidden to alter role for the
            # member because of it's role hierarchy.) -> will raise Forbidden and be caught by cmd error handler
            await member.add_roles(role, reason="Redeemed license.")
            # We add entry to db table LICENSED_MEMBERS (which we will checked periodically for expiration)
            # First we get the license duration so we can calculate expiration date
            license_duration = await self.bot.main_db.get_license_duration_hours(license)
            expiration_date = construct_expiration_date(license_duration)
            # In case where you successfully redeemed the role and it's still in database(not expired)
            # BUT someone manually removed the role, in that case when you try to redeem a valid license
            # for the said role you will get IntegrityError because LICENSED_ROLE_ID and MEMBER_ID have to
            # be unique (and the entry still exists in database).
            # Even when catched by remove role event leave this
            # TODO: On role remove remove from database too
            try:
                await self.bot.main_db.add_new_licensed_member(member.id, guild.id, expiration_date, role_id)
            except IntegrityError:
                # We remove the database entry because when role was remove the bot was
                # probably offline and couldn't register the role remove event
                await self.bot.main_db.delete_licensed_member(member.id, role_id)
                await self.bot.main_db.add_new_licensed_member(member.id, guild.id, expiration_date, role_id)
                await ctx.send("Someone removed the role manually from you but no worries,\n"
                               "since the license is valid we're just gonna reactivate it :)")

            # Remove guild license from database, so it can't be redeemed again
            await self.bot.main_db.delete_license(license)
            # Send message notifying user
            await ctx.send(f"License valid - adding role {role.mention} to {member.mention} in duration of {license_duration}h")
        else:
            await ctx.send("The license key you entered is invalid/deactivated.")


    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def generate(self, ctx, num: positive_integer = 3, license_role: discord.Role = None,
                       *, license_duration: license_duration = None):
        """
        Generates new guild licenses.

        All Arguments are optional, if not passed default guild values are used.

        Arguments are stacked, meaning you can't pass 'license_duration' without the first 2 arguments.
        On the other hand you can pass only 'num'.

        Example usages:
        generate
        generate 10
        generate 5 @role
        generate 7 @role 1w

        License duration is either a number representing hours or a string consisting of words in format:
        each word has to contain [integer][type format] format, entries are separated by space.

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
        ...
        """
        if num > 50:
            await ctx.send("Maximum number of licenses to generate at once is 50.")
            return

        # Check if the role is manageable by bot
        # Needed since bot isn't doing anything with the role, so no exception will occur.
        if license_role is not None and not ctx.me.top_role > license_role:
            await ctx.send("I can only manage roles **below** me in hierarchy.")
            return

        guild_id = ctx.guild.id

        # Maximum number of unused licenses
        max_licenses_per_guild = self.bot.config.get_maximum_unused_guild_licences()
        guild_licences_count = await self.bot.main_db.get_guild_license_total_count(max_licenses_per_guild+1, guild_id)
        if guild_licences_count == max_licenses_per_guild:
            await ctx.send(f"You have reached maximum number of unused licenses per guild: {max_licenses_per_guild}!")
            return
        if guild_licences_count + num > max_licenses_per_guild:
            await ctx.send(f"I can't generate since you will exceed the limit of {max_licenses_per_guild} licenses!\n"
                           f"Remaining licenses to generate: {max_licenses_per_guild-guild_licences_count}.")
            return

        if license_duration is None:
            license_duration = await self.bot.main_db.get_default_guild_license_duration_hours(guild_id)

        if license_role is None:
            licensed_role_id = await self.bot.main_db.get_default_guild_license_role_id(guild_id)
            license_role = ctx.guild.get_role(licensed_role_id)
            if license_role is None:
                await self.handle_missing_default_role(ctx, licensed_role_id)
                return

            generated = await self.bot.main_db.generate_guild_licenses(num, guild_id, licensed_role_id, license_duration)
        else:
            generated = await self.bot.main_db.generate_guild_licenses(num, guild_id, license_role.id, license_duration)

        count_generated = len(generated)
        await ctx.send(f"Successfully generated {count_generated} licenses for role {license_role.mention}"
                       f" in duration of {license_duration}h.\n"
                       f"Sending generated licenses in DM for quick use.")
        dm_content = "\n".join(generated)
        await ctx.author.send(f"Generated {count_generated} licenses for role **{license_role.name}** in "
                              f"guild **{ctx.guild.name}** in duration of {license_duration}h:\n"
                              f"{dm_content}")

    @commands.command(aliases=["licences"])
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def licenses(self, ctx, license_role: discord.Role = None):
        """
        Shows up to 10 licenses in DM.

        Shows licenses linked to license_role and your guild.
        If license_role is not passed then default guild role is used.

        Sends results in DM to the user who invoked the command.

        """
        # Currently fixed to up to 10
        # TODO: Perhaps add argument for it? Is it necessary?
        num = 10

        guild_id = ctx.guild.id
        if license_role is None:
            # If license role is not passed just use the guild default license role
            # We load it from database
            licensed_role_id = await self.bot.main_db.get_default_guild_license_role_id(guild_id)
            license_role = ctx.guild.get_role(licensed_role_id)
            if license_role is None:
                await self.handle_missing_default_role(ctx, licensed_role_id)
                return
            to_show = await self.bot.main_db.get_guild_licenses(num, guild_id, licensed_role_id)
        else:
            to_show = await self.bot.main_db.get_guild_licenses(num, guild_id, license_role.id)

        if len(to_show) == 0:
            await ctx.send("No available licenses for that role.")
            return

        dm_title = f"Showing licenses for role **{license_role.name}** in guild **{ctx.guild.name}**:"
        dm_content = "\n".join(to_show)
        await ctx.author.send(f"{dm_title}\n"
                              f"{dm_content}")

    @commands.command(alliases=["random_licenses"])
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def random_license(self, ctx, x: int = 1):
        """
        Shows random x guild licenses in DM.

        If x is not passed default value is 1.
        Maximum x is 10 (10 licenses to show).

        Sends results in DM to the user who invoked the command.

        """
        if x > 10:
            await ctx.send("Number can't be larger than 10!")
            return
        to_show = await self.bot.main_db.get_random_licenses(ctx.guild.id, x)
        if not to_show:
            await ctx.send("No licenses saved in db.")
            return

        table = texttable.Texttable(max_width=90)
        table.set_cols_dtype(["t", "t", "t"])
        table.set_cols_align(["c", "c", "c"])
        header = ("License", "Role", "Duration (h)")
        table.add_row(header)

        for entry in to_show:
            # Entry is in form ('I0QSZeyPJTy3H8tNsmUihKsn8JH48y', '617484493296631839', 720)
            try:
                role = ctx.guild.get_role(int(entry[1]))
                table.add_row((entry[0], role.name, entry[2]))
            except (ValueError, AttributeError):
                # Just in case if error in case role is None (deleted from guild) just show IDs from database
                table.add_row(entry)

        message = f"Showing {x} random licenses from guild '{ctx.guild.name}':\n{table.draw()}"
        await ctx.author.send(f"```{misc.maximize_size(message)}```")

    @commands.command(aliases=["data"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def member_data(self, ctx, member: discord.Member = None):
        """
        Shows active subscriptions of member.
        Sends result in DMs

        """
        if member is None:
            member = ctx.author

        table = texttable.Texttable(max_width=90)
        table.set_cols_dtype(["t", "t"])
        table.set_cols_align(["c", "c"])
        header = ("Licensed role", "Expiration date")
        table.add_row(header)

        all_active = await self.bot.main_db.get_member_data(ctx.guild.id, member.id)
        if not all_active:
            await ctx.send("Nothing to show.")
            return

        for entry in all_active:
            # Entry is in form ("license_id", "expiration_date)
            try:
                role = ctx.guild.get_role(int(entry[0]))
                table.add_row((role.name, entry[1]))
            except (ValueError, AttributeError):
                # Just in case if error in case role is None (deleted from guild) just show IDs from database
                table.add_row(entry)

        message = f"{member.name} active subscriptions in guild '{ctx.guild.name}':\n{table.draw()}"
        await ctx.author.send(f"```{misc.maximize_size(message)}```")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def delete_license(self, ctx, license):
        """
        Deletes specified license.
        Can delete only 1 at the time.

        """
        if await self.bot.main_db.is_valid_license(license, ctx.guild.id):
            await self.bot.main_db.delete_license(license)
            await ctx.send("License deleted.")
        else:
            await ctx.send("License not valid.")

    async def handle_missing_default_role(self, ctx, missing_role_id: int):
        """
        Guilds have a default license role that will be used if no role argument is
        passed when generating licenses. But it can happen that that role gets
        deleted while it's still in database (similar problem as in check_all_active_licenses)

        :param missing_role_id: role that is in db but is missing in guild

        TODO: add event on_guild_role_delete

        TODO: on startup/reconnect check if default role from db is valid

        """
        await ctx.send(f"Trying to use role with ID {missing_role_id} that was set "
                       f"as default role for guild {ctx.guild.name} but cannot find it"
                       f"anymore in the list of roles!")


def setup(bot):
    bot.add_cog(LicenseHandler(bot))
