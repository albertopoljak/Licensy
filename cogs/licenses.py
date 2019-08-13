import asyncio
import logging
from datetime import datetime, timedelta
from dateutil import parser
from discord.ext import commands
from discord.errors import Forbidden
import discord.utils
from helpers.converters import positive_integer, license_duration
from helpers.errors import RoleNotFound

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
            logger.info("Checking all licenses...")
            await self.check_all_active_licenses()
            logger.info("License check done.")
            # Sleep 5 minutes
            await asyncio.sleep(300)

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

        TODO: add event on_guild_remove

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
            raise Exception(f"Fatal exception. Guild {guild_id} loaded from database cannot be found in bot guilds!")
        member = guild.get_member(member_id)
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
        guild_id = guild.id
        default_prefix = self.bot.config.get_default_prefix()
        insert_guild_query = "INSERT INTO GUILDS(GUILD_ID, PREFIX) VALUES(?,?)"
        await self.bot.main_db.connection.execute(insert_guild_query, (guild_id, default_prefix))
        await self.bot.main_db.connection.commit()

    @commands.command(aliases=["activate"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def redeem(self, ctx, license):
        """
        License is checked for validity in database, if it's valid get the
        role linked to the database and assign the role to the member.
        :param license: License to redeem

        TODO: Better security (right now license is visible in plain sight in guild)
        """
        guild = ctx.guild
        author = ctx.author
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
            if role in author.roles:
                # We notify user that he already has the role, we also show him the expiration date
                expiration_date = await self.bot.main_db.get_member_license_expiration_date(author.id, role_id)
                remaining_time = LicenseHandler.remaining_time(expiration_date)
                await ctx.send(f"{author.mention} you already have an active subscription for the {role.mention} role!"
                               f"\nIt's valid for another {remaining_time}")
                return
            # We add the role to the member, we do this before adding/removing stuff from db
            # just in case the bot doesn't have perms and throws exception (we already
            # checked for bot_has_permissions(manage_roles=True) but it can happen that bot has
            # that permission and check is passed but it's still forbidden to alter role for the
            # member because of it's role hierarchy.) -> will raise Forbidden and be caught by cmd error handler
            await author.add_roles(role, reason="Redeemed license.")
            # We add entry to db table LICENSED_MEMBERS (which we will checked periodically for expiration)
            # First we get the license duration so we can calculate expiration date
            license_duration = await self.bot.main_db.get_license_duration_hours(license)
            expiration_date = LicenseHandler.construct_expiration_date(license_duration)
            await self.bot.main_db.add_new_licensed_member(author.id, guild.id, expiration_date, role_id)
            # Remove guild license from database, so it can't be redeemed again
            await self.bot.main_db.delete_license(license)
            # Send message notifying user
            await ctx.send(f"License valid - adding role {role.mention} to {author.mention}")
        else:
            await ctx.send("The license key you entered is invalid/deactivated.")

    @commands.command(aliases=["create"])
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def generate(self, ctx, num: positive_integer = 1, license_role: discord.Role = None,
                       *, license_duration: license_duration = None):
        """
        TODO: allow passing arguments in different order

        """
        if num > 50:
            await ctx.send("Maximum number of licenses to generate at once is 50.")
            return

        guild_id = ctx.guild.id

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

    @commands.command(aliases=["show", "print"])
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def licenses(self, ctx, num: positive_integer = 10, license_role: discord.Role = None):
        """
        TODO: allow passing arguments in different order

        """
        if num > 50:
            await ctx.send("Maximum number of licenses to show at once is 50.")
            return

        guild_id = ctx.guild.id
        if license_role is None:
            licensed_role_id = await self.bot.main_db.get_default_guild_license_role_id(guild_id)
            license_role = ctx.guild.get_role(licensed_role_id)
            if license_role is None:
                await self.handle_missing_default_role(ctx, licensed_role_id)
                return
            to_show = await self.bot.main_db.get_guild_licenses(num, guild_id, licensed_role_id)
        else:
            to_show = await self.bot.main_db.get_guild_licenses(num, guild_id, license_role.id)

        dm_title = f"Showing licenses for role **{license_role.name}** in guild **{ctx.guild.name}**:"
        dm_content = "\n".join(to_show)
        await ctx.author.send(f"{dm_title}\n"
                              f"{dm_content}")

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

    @staticmethod
    def construct_expiration_date(license_duration_hours: int) -> datetime:
        """
         Return format:
        Y-M-D H:M:S.mS
        :param license_duration_hours: int hours to be added to current date
        :return: datetime current time incremented by param license_duration_hours

        """
        expiration_date = datetime.now() + timedelta(hours=license_duration_hours)
        return expiration_date

    @staticmethod
    def remaining_time(expiration_date: str) -> str:
        """
        :param expiration_date: string in format Y-M-D H:M:S.mS
        :return: timedelta difference between expiration_date and current time

        """
        # Convert string to datetime
        expiration_datetime = datetime.strptime(expiration_date, "%Y-%m-%d %H:%M:%S.%f")
        # timedelta object
        difference = expiration_datetime-datetime.now()
        # difference has ms in it so we remove it here for nicer display
        difference = str(difference).split(".")[0]
        return difference


def setup(bot):
    bot.add_cog(LicenseHandler(bot))
