import discord
from discord.ext import commands
from helpers.embed_handler import success_embed, failure_embed
from helpers.misc import tail
from helpers.paginator import Paginator


class BotOwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update(self, ctx, *, msg=None):
        if msg is None:
            msg = """Update in progress.
                    Non breaking changes that will not affect bot usage/performance."""
        await self.bot.change_presence(activity=discord.Game(name=msg))
        await ctx.send(success_embed("Successfully changed status.", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def playing(self, ctx, *, game):
        await self.bot.change_presence(activity=discord.Game(name=game))
        msg = f"Successfully set presence to **Playing {game}**."
        await ctx.send(embed=success_embed(msg, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def streaming(self, ctx, name, url):
        """
        Discord py currently only supports twitch urls.

        """
        if "//www.twitch.tv" not in url:
            await ctx.send(embed=failure_embed("Only twitch urls supported!"))
            return
        await self.bot.change_presence(activity=discord.Streaming(name=name, url=url))
        msg = f"Successfully set presence to **Streaming {name}**."
        await ctx.send(embed=success_embed(msg, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def listening(self, ctx, *, song):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=song))
        msg = f"Successfully set presence to **Listening to {song}**."
        await ctx.send(embed=success_embed(msg, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def watching(self, ctx, *, movie):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=movie))
        msg = f"Successfully set presence to **Watching {movie}**."
        await ctx.send(embed=success_embed(msg, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_config(self, ctx):
        """
        Reloads json config.

        """
        self.bot.config.reload_config()
        msg = "Successfully reloaded config."
        await ctx.send(embed=success_embed(msg, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def show_log(self, ctx, lines=100):
        """
        Shows last n lines from log.txt

        Max lines 10 000.
        Sends multiple messages at once if needed.
        """
        if lines > 10_000:
            lines = 10_000

        log = "".join(tail(lines))
        await Paginator.paginate(self.bot, ctx.author, ctx.author, log,
                                 title=f"Last {lines} log lines.\n\n", prefix="```DNS\n")


def setup(bot):
    bot.add_cog(BotOwnerCommands(bot))
