import logging
import random
import asyncio
import discord
from discord.ext import commands
from discord.errors import NotFound
from helpers.converters import positive_integer

logger = logging.getLogger(__name__)


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx, duration_minutes: positive_integer):
        duration_minutes *= 60
        if duration_minutes > 1440:
            await ctx.send(f"Maximum duration is 24h!", delete_after=5)
            return
        elif duration_minutes < 1:
            await ctx.send("Minimum duration is 1min!", delete_after=5)
            return

        description = "React to this message to enter the giveaway and a chance to win license!"
        embed = discord.Embed(title="Giveaway!", description=description, color=ctx.me.top_role.color)
        emoji = "🎉"
        message = await ctx.send(embed=embed)
        await message.add_reaction(emoji)

        await asyncio.sleep(duration_minutes)

        try:
            done_message = await ctx.channel.fetch_message(message.id)
        except NotFound:
            logger.info(f"Event message deleted! Event canceled! Guild:{ctx.guild.id} {ctx.guild.name}, "
                        f"channel: {ctx.channel.id} {ctx.channel.name}")
            return

        for reaction in done_message.reactions:
            if str(reaction.emoji) == emoji:
                choices = []
                async for user in reaction.users():
                    if not user.bot:
                        choices.append(user)
                if choices:
                    winner = random.choice(choices)
                    edit_description = f"{description}\n{winner.mention} has won the raffle!"
                    edit_embed = discord.Embed(title="Giveaway!", description=edit_description, color=ctx.me.top_role.color)
                    await message.edit(embed=edit_embed)
                    await ctx.send(f"{winner.mention} has won the raffle.", delete_after=10)
                else:
                    await ctx.send("Giveaway has finished, no one reacted.")
            break


def setup(bot):
    bot.add_cog(Games(bot))
