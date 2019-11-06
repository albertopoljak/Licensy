import logging
import random
import asyncio
import discord
from discord.ext import commands
from discord.errors import NotFound
from helpers.converters import positive_integer
from helpers.embed_handler import info, failure

logger = logging.getLogger(__name__)


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def giveaway(self, ctx, duration_minutes: positive_integer, channel: discord.TextChannel):
        if duration_minutes > 1440:
            await ctx.send(embed=failure("Maximum duration is 24h!"), delete_after=5)
            return

        description = "React to this message to enter the giveaway and a chance to win license!"
        event_title = "Giveaway!"
        emoji = "🎉"
        message = await channel.send(embed=info(description, ctx.me, title=event_title))
        await message.add_reaction(emoji)

        await asyncio.sleep(duration_minutes*60)

        try:
            done_message = await channel.fetch_message(message.id)
        except NotFound:
            logger.info(f"Event message deleted! Event canceled! Guild:{ctx.guild.id} {ctx.guild.name}, "
                        f"channel: {channel.id} {channel.name}")
            return

        for reaction in done_message.reactions:
            if str(reaction.emoji) == emoji:
                choices = []
                async for user in reaction.users():
                    if not user.bot:
                        choices.append(user)
                if choices:
                    winner = random.choice(choices)
                    edit_description = f"Giveaway has finished,\n{winner.mention} has won the raffle!"
                    await message.edit(embed=info(edit_description, ctx.me, title=event_title))
                    await channel.send(f"{winner.mention} has won the raffle.", delete_after=10)
                else:
                    edit_description = "Giveaway has finished, no one reacted :("
                    await message.edit(embed=info(edit_description, ctx.me, title=event_title))
            break


def setup(bot):
    bot.add_cog(Games(bot))
