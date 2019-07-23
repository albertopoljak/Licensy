from discord.ext import commands
import discord.utils
from helpers.misc import positive_integer
from helpers.errors import RoleNotFound


class LicenseHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot ready, checking all licenses...")
        await self.check_all_active_licenses()
        print("License check done.")

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

        """
        async with self.bot.main_db.connection.execute("SELECT * FROM LICENSED_MEMBERS") as cursor:
            async for row in cursor:
                member_id = int(row[0])
                member_guild_id = int(row[1])
                expiration_date = int(row[2])
                licensed_role_id = int(row[3])
                if await self.has_license_expired(expiration_date):
                    print(f"Expired license for {member_id}")
                    await self.remove_role(member_id, member_guild_id, licensed_role_id)

    async def has_license_expired(self, expiration_date):
        """
        Check if param expiration date is in past related to the current date.
        If it is in past then license is considered expired.
        :param expiration_date: PLACEHOLDER, currently always returns FALSE
        :return: True if license is expired, False otherwise

        """
        print(expiration_date)
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
        member = guild.get_member(member_id)
        member_role = discord.utils.get(member.roles, id=licensed_role_id)
        if member_role is None:
            raise RoleNotFound(f"Can't remove licensed role {member_role} for {member.mention}."
                               f"Role not found ")
        else:
            await member.remove_roles(member_role)
            await member.send(f"Your license in guild **{guild}** has expired "
                              f"for the following role: **{member_role}** ")

    @commands.command()
    @commands.guild_only()
    async def redeem(self, ctx, license):
        """
        License is checked for validity in database, if it's valid get the
        role linked to the database and assign the role to the member.
        :param license: License to redeem

        TODO: Better security (right now license is visible in plain sight in guild)

        """
        guild = ctx.guild
        if await self.is_valid_license(license, guild.id):
            # Add role to the user
            # First we get the role linked to the license
            role_id = await self.bot.main_db.get_license_role_id(license)
            role = ctx.guild.get_role(role_id)
            # Finally we add the role to the user
            await ctx.author.add_roles(role, reason="Redeemed license.")
            # Remove guild license from database
            await self.bot.main_db.drop_guild_license(license, guild.id)
            # Send message notifying user
            await ctx.send(f"License valid - adding role {role.mention} to {ctx.author}")
        else:
            await ctx.send("The license key you entered is invalid/deactivated.")

    async def is_valid_license(self, license: str, guild_id: int) -> bool:
        """
        :param license: License to check
        :param guild_id:
        :return: True if license is valid, False otherwise

        TODO: guild_id is actually not needed since LICENSE is unique in the database, refactor

        TODO: query doesn't require all rows with *, we can just use column LICENSE

        """
        async with self.bot.main_db.connection.execute("SELECT * FROM GUILD_LICENSES WHERE GUILD_ID=?",
                                                       (guild_id,)) as cursor:
            async for row in cursor:
                db_license = row[0]
                db_guild_id = int(row[1])
                if db_license == license and db_guild_id == guild_id:
                    return True
        return False

    @commands.command(aliases=["create"])
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def generate(self, ctx, num: positive_integer = 1, license_role: discord.Role = None):
        if num > 100:
            await ctx.send("Maximum number of licenses to generate at once is 100.")
            return

        guild_id = ctx.guild.id
        if license_role is None:
            licensed_role_id = await self.bot.main_db.get_default_guild_license_role_id(guild_id)
            license_role = ctx.guild.get_role(licensed_role_id)
            if license_role is None:
                await self.handle_missing_default_role(ctx, licensed_role_id)
                return

            generated = await self.bot.main_db.generate_guild_licenses(num, guild_id, licensed_role_id)
        else:
            generated = await self.bot.main_db.generate_guild_licenses(num, guild_id, license_role.id)

        count_generated = len(generated)
        await ctx.send(f"Successfully generated {count_generated} licenses for role {license_role.mention}.")
        dm_content = "\n".join(generated)
        await ctx.author.send(f"Generated {count_generated} licenses for role {license_role.name}:\n"
                              f"{dm_content}")

    @commands.command(aliases=["licences", "show"])
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.has_permissions(administrator=True)
    async def licenses(self, ctx, num: positive_integer = 10, license_role: discord.Role = None):
        if num > 100:
            await ctx.send("Maximum number of licenses to show at once is 100.")
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

        dm_title = f"Showing licenses for role {license_role.name}:"
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


def setup(bot):
    bot.add_cog(LicenseHandler(bot))
