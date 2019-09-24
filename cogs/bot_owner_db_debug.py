import logging
import discord
from discord.ext import commands
from helpers import misc
from helpers.converters import license_duration
from helpers.licence_helper import construct_expiration_date
from helpers.embed_handler import success_embed, failure_embed, info_embed

logger = logging.getLogger(__name__)


class BotOwnerDbDebug(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_guild_join(self, ctx, guild_prefix, guild_id: int = None):
        """
        Manually add guild to the database
        :param guild_prefix: Every guild will have it's own prefix
        :param guild_id: To manually add a guild without being in it.
        """
        if guild_id is None:
            await self.bot.main_db.setup_new_guild(ctx.guild.id, guild_prefix)
            await ctx.send(embed=success_embed("Done", ctx.me))
        else:
            if self.bot.get_guild(guild_id) is None:
                await ctx.send(embed=failure_embed("Guild doesn't exist"))
            else:
                await self.bot.main_db.setup_new_guild(guild_id, guild_prefix)
                await ctx.send(embed=success_embed("Done", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_new_licensed_member(self, ctx, member: discord.Member, role: discord.Role,
                                        *, license_dur: license_duration):
        expiration_date = construct_expiration_date(license_dur)
        await self.bot.main_db.add_new_licensed_member(member.id, ctx.guild.id, expiration_date, role.id)
        await ctx.send(embed=success_embed("Done", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_delete_licensed_member(self, ctx, member: discord.Member, licensed_role: discord.Role):
        await self.bot.main_db.delete_licensed_member(member.id, licensed_role.id)
        await ctx.send(embed=success_embed("Done", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_get_guild_license_total_count(self, ctx):
        count = await self.bot.main_db.get_guild_license_total_count(ctx.guild.id)
        await ctx.send(embed=info_embed(count, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def valid(self, ctx, license):
        """
        Checks if passed license is valid

        """
        if await self.bot.main_db.is_valid_license(license, ctx.guild.id):
            await ctx.send(embed=success_embed("License is valid", ctx.me))
        else:
            await ctx.send(embed=failure_embed(f"License is not valid."))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_remove_all_guild_data(self, ctx, guild_too: int = 0):
        await self.bot.main_db.remove_all_guild_data(ctx.guild.id, guild_too)
        await ctx.send(embed=success_embed("Done", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_remove_all_guild_licenses(self, ctx):
        await self.bot.main_db.remove_all_guild_licenses(ctx.guild.id)
        await ctx.send(embed=success_embed("Done", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def show_guilds(self, ctx):
        limit = 100
        to_print = ["\nJoined guilds:\n\n"]
        for i, guild in enumerate(self.bot.guilds):
            if i == limit:
                break
            to_print.append(f"{guild.id}:{guild.name}\n")

        string_output = "".join(to_print)
        await ctx.send(embed=success_embed(misc.maximize_size(string_output), ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def show_db_guilds(self, ctx):
        to_print = ["\nTable GUILDS:\n\n"]
        cur = await self.bot.main_db.connection.cursor()

        async def print_cursor(cursor):
            results = await cursor.fetchall()
            for row in results:
                for record in range(len(row)):
                    to_print.append(f"{row[record]} ")
                to_print.append("\n")

        await cur.execute("SELECT * FROM GUILDS LIMIT 100")
        await print_cursor(cur)
        await cur.close()

        string_output = "".join(to_print)
        await ctx.send(embed=success_embed(misc.maximize_size(string_output), ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def show_db_active_licensed_members(self, ctx):
        to_print = ["\nTable LICENSED_MEMBERS:\n\n"]
        cur = await self.bot.main_db.connection.cursor()

        async def print_cursor(cursor):
            results = await cursor.fetchall()
            for row in results:
                for record in range(len(row)):
                    to_print.append(f"{row[record]} ")
                to_print.append("\n")

        await cur.execute("SELECT * FROM LICENSED_MEMBERS LIMIT 100")
        await print_cursor(cur)
        await cur.close()

        string_output = "".join(to_print)
        await ctx.send(embed=success_embed(misc.maximize_size(string_output), ctx.me))


def setup(bot):
    bot.add_cog(BotOwnerDbDebug(bot))
