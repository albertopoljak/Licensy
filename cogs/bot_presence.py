import discord
from discord.ext import commands


class BotPresence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def playing(self, ctx, *, game):
        await self.bot.change_presence(activity=discord.Game(name=game))
        await ctx.send(f"Successfully set presence to **Playing {game}**.")
        self.bot.config.update_status(game)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def streaming(self, ctx, name, url):
        """
        Discord py currently only supports twitch urls.
        """
        await self.bot.change_presence(activity=discord.Streaming(name=name, url=url))
        await ctx.send(f"Successfully set presence to **Streaming {name}**.")
        self.bot.config.update_status(name)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def listening(self, ctx, *, song):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=song))
        await ctx.send(f"Successfully set presence to **Listening to {song}**.")
        self.bot.config.update_status(song)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def watching(self, ctx, *, movie):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=movie))
        await ctx.send(f"Successfully set presence to **Watching {movie}**.")
        self.bot.config.update_status(movie)


def setup(bot):
    bot.add_cog(BotPresence(bot))
