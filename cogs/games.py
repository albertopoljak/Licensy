import logging
import random
import asyncio
import discord
from discord.ext import commands
from helpers.converters import license_duration as duration

logger = logging.getLogger(__name__)


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx, duration_seconds: duration):
        if duration_seconds > 1440:
            await ctx.send("Maximum duration is 24h!", delete_after=3)
            return

        everyone_role = ctx.guild.default_role
        await ctx.send(f"Giveaway has started! {everyone_role.mention}", delete_after=60)

        description = "React to this message to enter the giveaway and a chance to win license!"
        embed = discord.Embed(title="Giveaway!", description=description, color=ctx.me.top_role.color)
        #emoji = "🎉"
        emoji = ":arrow_backward:"
        message = await ctx.send(embed=embed)
        await message.add_reaction(emoji)

        await ctx.message.delete()
        await asyncio.sleep(duration_seconds)

        done_message = await ctx.channel.fetch_message(message.id)
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
