import math
import logging
import traceback
from discord.ext import commands
from discord.errors import Forbidden
from helpers.errors import RoleNotFound, DefaultGuildRoleNotSet, DatabaseMissingData
from helpers.embed_handler import failure_embed, log_embed, traceback_embed

logger = logging.getLogger(__name__)


class CmdErrors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # If command has local error handler, return
        if hasattr(ctx.command, "on_error"):
            return

        # Get the original exception
        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandNotFound):
            await ctx.send(embed=failure_embed("Command not found."))
            return

        if isinstance(error, commands.BotMissingPermissions):
            """
            Note that this is only for checks of the command , specifically for bot_has_permissions 
            example @commands.bot_has_permissions(administrator=True)
            It will not work for example if in command role.edit is called but bot doesn't have manage role permission.
            In that case a simple "Forbidden" will be raised.
            
            """
            missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_perms]
            if len(missing) > 2:
                fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = " and ".join(missing)
            _message = f"I need the **{fmt}** permission(s) to run this command."
            await ctx.send(embed=failure_embed(_message))
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(embed=failure_embed("This command has been disabled."))
            return

        if isinstance(error, commands.CommandOnCooldown):
            # Cooldowns are ignored for developers
            if not await self.developer_bypass(ctx):
                msg = f"This command is on cooldown, please retry in {math.ceil(error.retry_after)}s."
                await ctx.send(embed=failure_embed(msg))
            return

        if isinstance(error, commands.MissingPermissions):
            """
            Note that this is only for checks of the command , example @commands.has_permissions(administrator=True)
            MissingPermissions is raised if check for permissions of the member who invoked the command has failed.
            
            """
            # Developers can bypass guild permissions
            if not await self.developer_bypass(ctx):
                missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_perms]
                if len(missing) > 2:
                    fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
                else:
                    fmt = " and ".join(missing)
                _message = f"You need the **{fmt}** permission(s) to use this command."
                await ctx.send(embed=failure_embed(_message))
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send(embed=failure_embed(f"Invalid command input: {error}"))
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(embed=failure_embed("This command cannot be used in direct messages."))
            except Forbidden:
                pass
            return

        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed=failure_embed("You do not have permission to use this command."))
            return

        if isinstance(error, Forbidden):
            # 403 FORBIDDEN (error code: 50013): Missing Permissions
            if error.code == 50013:
                msg = (f"{error}.\n"
                       f"Check role hierarchy - I can only manage roles below me.")
                try:
                    await ctx.send(embed=failure_embed(msg))
                except Forbidden:
                    # Forbidden can also mean no permissions to send to that channel
                    # Ignore so we don't get useless errors
                    return

            # 403 FORBIDDEN (error code: 50007): Cannot send messages to this user.
            elif error.code == 50007:
                msg = (f"{error}.\n"
                       f"Hint: Disabled DMs?")
                await ctx.send(embed=failure_embed(msg))

            else:
                await ctx.send(embed=failure_embed(f"{error}."))
            return

        if isinstance(error, RoleNotFound):
            await ctx.send(embed=failure_embed(error.message))
            return

        if isinstance(error, DefaultGuildRoleNotSet):
            new_msg = error.message.replace("{prefix}", ctx.prefix)
            await ctx.send(embed=failure_embed(f"Trying to use default guild license but: {new_msg}"))
            return

        if isinstance(error, DatabaseMissingData):
            await ctx.send(embed=failure_embed(f"Database error: {error.message}"))
            await self.log_traceback(ctx, error)
            return

        await self.log_traceback(ctx, error)
        msg = (f"Ignoring exception **{error.__class__.__name__}** that happened while processing command "
               f"**{ctx.command}**:\n{error}")
        await ctx.send(embed=failure_embed(msg))

    async def log_traceback(self, ctx, error):
        error_type = type(error)
        exception_message = f"Ignoring {error_type} exception in command '{ctx.command}':{error}"
        traceback_message = traceback.format_exception(etype=error_type, value=error, tb=error.__traceback__)
        logger.critical(f"{exception_message}")
        logger.critical(traceback_message)
        if self.bot.is_ready():
            log_channel = self.bot.get_channel(self.bot.config.get_developer_log_channel_id())
            embed = log_embed(exception_message, ctx=ctx, title="Command error!")
            trace_embed = traceback_embed(traceback_message)
            if log_channel is not None:
                await log_channel.send(embed=embed)
                await log_channel.send(embed=trace_embed)

    async def developer_bypass(self, ctx):
        """
        Developers can bypass guild permissions/ cooldowns etc.
        Re-invokes the command.
        :param ctx: ctx to re-invoke the command from (if the author is bot developer)
        :return: Bool if developer or not.
        """
        # Developers can bypass guild permissions
        if ctx.message.author.id in self.bot.config.get_developers().values():
            # reinvoke() bypasses error handlers so we surround it with try/catch and just
            # send errors to ctx
            try:
                await ctx.reinvoke()
            except Exception as e:
                await ctx.send(embed=failure_embed(str(e)))
            return True
        else:
            return False


def setup(bot):
    bot.add_cog(CmdErrors(bot))
