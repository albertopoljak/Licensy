from helpers.converters import license_duration
import logging
import discord
from aiosqlite import IntegrityError
from discord.ext import commands
from helpers.embed_handler import success_embed, failure_embed

logger = logging.getLogger(__name__)


class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def prefix(self, ctx, *, prefix):
        """
        Changes guild prefix.
        Maximum prefix size is 5 characters.

        """
        try:
            await self.bot.main_db.change_guild_prefix(ctx.guild.id, prefix)
        except IntegrityError:
            await ctx.send(embed=failure_embed("Prefix is too long! Maximum of 5 characters please."))
            return

        await ctx.send(embed=success_embed(f"Successfully changed prefix to **{prefix}**", ctx.me))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def default_role(self, ctx, role: discord.Role):
        """
        Changes guild default license role.

        When creating new license, and role is not passed, this is the default role the license will use.
        Role tied to license is the role that the member will get when he redeems it.

        """
        # Check if the role is manageable by bot
        if not ctx.me.top_role > role:
            await ctx.send(embed=failure_embed("I can only manage roles **below** me in hierarchy."))
            return
        await self.bot.main_db.change_default_guild_role(ctx.guild.id, role.id)
        await ctx.send(embed=success_embed(f"{role.mention} set as default!", ctx.me))

    @commands.command(aliases=["license_expiration", "expiration"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
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
        await ctx.send(embed=success_embed(f"Default license expiration set to **{expiration}h**!", ctx.me))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def guild_info(self, ctx):
        """
        Shows database data for the guild.

        Message contains guild prefix, default license role and default license expiration time.

        """
        prefix, role_id, expiration = await self.bot.main_db.get_guild_info(ctx.guild.id)
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
                await ctx.send(embed=failure_embed(msg))
            else:
                default_license_role = default_license_role.mention
        else:
            default_license_role = "**Not set!**"

        msg = (f"Database guild info:\n"
               f"Prefix: **{prefix}**\n"
               f"Default license role: {default_license_role}\n"
               f"Default license expiration time: **{expiration}h**")
        await ctx.send(embed=success_embed(msg, ctx.me))


def setup(bot):
    bot.add_cog(Guild(bot))
