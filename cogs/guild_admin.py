from discord.ext import commands


class BotPresence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def prefix(self, ctx, *, prefix):
        await self.bot.main_db.change_guild_prefix(ctx.guild.id, prefix)
        await ctx.send(f"Successfully changed prefix to **{prefix}**")


def setup(bot):
    bot.add_cog(BotPresence(bot))
