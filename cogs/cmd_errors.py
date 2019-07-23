import discord
import traceback
import math
from discord.ext import commands
from discord.errors import Forbidden
from helpers.errors import RoleNotFound


class CmdErrors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # if command has local error handler, return
        if hasattr(ctx.command, "on_error"):
            return

        # get the original exception
        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.BotMissingPermissions):
            missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_perms]
            if len(missing) > 2:
                fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = " and ".join(missing)
            _message = f"I need the **{fmt}** permission(s) to run this command."
            await ctx.send(_message)
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send("This command has been disabled.")
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown, please retry in {math.ceil(error.retry_after)}s.")
            return

        if isinstance(error, commands.MissingPermissions):
            missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_perms]
            if len(missing) > 2:
                fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = " and ".join(missing)
            _message = f"You need the **{fmt}** permission(s) to use this command."
            await ctx.send(_message)
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send("Invalid command input.")
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send("This command cannot be used in direct messages.")
            except discord.Forbidden:
                pass
            return

        if isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permission to use this command.")
            return

        if isinstance(error, Forbidden):
            await ctx.send("I don't have the required permissions to do this.")
            return

        if isinstance(error, RoleNotFound):
            await ctx.send(error.message)
            return

        print(f"Ignoring {type(error)} exception in command '{ctx.command}':{error}")
        traceback.print_exception(type(error), error, error.__traceback__)


def setup(bot):
    bot.add_cog(CmdErrors(bot))
