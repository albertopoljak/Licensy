import discord
from discord.ext import commands


class BotOwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO:
    # @commands.check(my_function)
    # # Check against your own function that returns those able to use your command
    # instead of is_owner, use my_function to check multiple developers

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

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_config(self, ctx):
        self.bot.config.reload_config()
        await ctx.send("Successfully reloaded config.")


def setup(bot):
    bot.add_cog(BotOwnerCommands(bot))
