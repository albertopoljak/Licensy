import discord
from discord.ext import commands
from helpers import licence_generator


class DbTest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setup(self, ctx, guild_prefix, default_license_role: discord.Role):
        """
        For testing purposes
        Usually the bot will create table in on_guild_join event but since
        we're testing we can't waste time on that.
        :param guild_prefix: Every guild will have it's own prefix
        :param default_license_role:  default role to link with license if no role is passed
                                      when calling command 'generate'

        """
        guild_id = ctx.guild.id
        default_license_role_id = default_license_role.id
        licenses = licence_generator.generate(3)

        insert_guild_query = "INSERT INTO GUILDS(GUILD_ID, PREFIX, DEFAULT_LICENSE_ROLE_ID) VALUES(?,?,?)"
        await self.bot.main_db.connection.execute(insert_guild_query, (guild_id, guild_prefix, default_license_role_id))

        insert_liceses_query = "INSERT INTO GUILD_LICENSES(LICENSE, GUILD_ID, LICENSED_ROLE_ID) VALUES(?,?,?)"
        for license in licenses:
            await self.bot.main_db.connection.execute(insert_liceses_query, (license, guild_id, default_license_role_id))
        await self.bot.main_db.connection.commit()

    @commands.command()
    async def db(self, ctx):
        """
        Prints entire database
        For testing purposes

        """
        async def print_cursor(cursor):
            results = await cursor.fetchall()
            for row in results:
                for record in range(len(row)):
                    print(row[record], end=" ")
                print()

        cur = await self.bot.main_db.connection.cursor()

        await cur.execute("SELECT * FROM GUILDS")
        print("\nTable GUILDS:")
        await print_cursor(cur)

        await cur.execute("SELECT * FROM LICENSED_MEMBERS")
        print("\nTable LICENSED_MEMBERS:")
        await print_cursor(cur)

        await cur.execute("SELECT * FROM GUILD_LICENSES")
        print("\nTable GUILD_LICENSES:")
        await print_cursor(cur)

        await cur.close()

    @commands.command()
    async def test_add(self, ctx, guild_id, license):
        """"
        Insert passed license into database, license is tied to guild_id and fixed role ID 12345

        """
        query = "INSERT INTO GUILD_LICENSES(LICENSE, GUILD_ID, LICENSED_ROLE_ID) VALUES(?,?,?)"
        cur = await self.bot.main_db.connection.cursor()
        await cur.execute(query, (license, guild_id, 12345))
        await cur.close()
        await self.bot.main_db.connection.commit()

    @commands.command()
    async def valid(self, ctx, license):
        """
        Checks if passed license is valid

        """
        if await self.bot.main_db.is_valid_license(license, ctx.guild.id):
            await ctx.send(f"Valid")
        else:
            await ctx.send(f"Invalid")


def setup(bot):
    bot.add_cog(DbTest(bot))
