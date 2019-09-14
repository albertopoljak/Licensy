import logging
from discord.ext import commands
from discord.ext.commands import MinimalHelpCommand
from helpers.embed_handler import info_embed

logger = logging.getLogger(__name__)


class PrettyHelpCommand(MinimalHelpCommand):
    def get_ending_note(self):
        command_name = self.invoked_with
        return ("Type {0}{1} <command> for more info on a command.\n"
                "You can also type {0}{1} <category> for more info on a category.").format(self.clean_prefix, command_name)

    def get_opening_note(self):
        if self.context.author.guild_permissions.administrator:
            return
        else:
            return "Commands that you have no permission for are hidden."

    def add_bot_commands_formatting(self, commands, heading):
        if commands:
            max_length = 19
            outputs = [f"  {c.name}{' ' * (max_length - len(c.name))}{c.short_doc}" for c in commands]
            joined = "\n".join(outputs)
            self.paginator.add_line(heading)
            self.paginator.add_line(joined)

    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(f"```{page}```")


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = PrettyHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        """
        Revert to default help command in case cog is unloaded

        """
        self.bot.help_command = self._original_help_command

    @commands.command()
    async def faq(self, ctx):
        """
        Show common Q/A about bot and it's usage.

        """
        disclaimer = ("Disclaimer: Bot is currently in alpha phase.\n"
                      "I am aware of certain security limitations (example points 1&2) "
                      "and I'll be working on improving it. Please let me know which features"
                      "/improvements you want so I can focus on those (use support command).")

        bot_faq = ("**1. If bot gets kicked/banned do I lose all my data?**\n"
                   "All of the guild data is immediately deleted from the database.\n\n"

                   "**2. What happens if I delete a role or remove it manually from a member?**\n"
                   "If that role is tied to any licenses/active subscriptions "
                   "they are immediately deleted from the database.\n\n"

                   "**3. What is the precision of role expiration?**\n"
                   "Bot checks for expired licenses on startup and each 10 minutes after startup.\n\n"

                   "**4. Who can view/generate guild licenses?**\n"
                   "Only those who have role administrator in the guild.\n\n"

                   "**5. How are licenses generated, are they unique?**\n"
                   "They are completely unique, comprised of 30 randomly generated characters.\n\n"

                   "**6. What's the maximum for role expire time?**\n"
                   "Bot is coded in a way that theoretically there is no limit, "
                   "but to keep things in sane borders the maximum time for expiry date is 12 months.\n\n"

                   "**7. How many licenses per guild?**\n"
                   "You can have unlimited subscribed members with each having unlimited subscribed roles"
                   " but there is a limit for unactivated licenses which is 100 per guild.")
        await ctx.send(embed=info_embed(f"{bot_faq}", ctx.me, title=disclaimer))


def setup(bot):
    bot.add_cog(Help(bot))
