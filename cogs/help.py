import logging
import discord
from discord.ext import commands
from helpers.embed_handler import info
from helpers.misc import embed_space, get_top_role_color

logger = logging.getLogger(__name__)


class PrettyHelpCommand(commands.MinimalHelpCommand):
    """
    Custom help command.
    See MinimalHelpCommand and it's parents for more info on overwritten methods.

    Sends the help as embed with color of the bot top color (works in DM too).
    Each command name/explanation is in one line, each marked as `code-line` and it's formatted in a way that
    names are left aligned and descriptions are also left aligned but moved for N spaces from names so that all
    descriptions start on the visually same line.

    Calling it in guild will hide the commands that you have no access too.
    Calling it in DMs will show you all commands.
    Hidden commands are always hidden.
    """

    def get_ending_note(self):
        command_name = self.invoked_with
        return "Type {0}{1} <command> for more info on a command.\n".format(self.clean_prefix, command_name)

    def get_opening_note(self):
        prefix = "If you like the bot please consider donating or starring the Github repository, ty :)"

        if self.context.guild is None or self.context.author.guild_permissions.administrator:
            return prefix
        else:
            return prefix + "\nCommands that you have no permission for are **hidden**:"

    def add_bot_commands_formatting(self, commands, heading):
        if commands:
            max_length = 19
            outputs = [f"`  {c.name}{embed_space * (max_length - len(c.name))}{c.short_doc}`" for c in commands]
            joined = "\n".join(outputs)
            self.paginator.add_line(f"\n**__{heading}__**")
            self.paginator.add_line(joined)

    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(description=page, color=get_top_role_color(self.context.me))
            await destination.send(embed=embed)

    async def send_bot_help(self, mapping):
        ctx = self.context
        # I want to verify_checks if it's called in guild but don't want it in DMs
        if ctx.guild is None:
            # Temporally disable verify checks then enable them again (alternative would be a lot of DRY breaking).
            self.verify_checks = False
            await super().send_bot_help(mapping)
            self.verify_checks = True
        else:
            await super().send_bot_help(mapping)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = PrettyHelpCommand()
        bot.help_command.cog = self
        self.github_permissions_link = "https://github.com/albertopoljak/Licensy#permissions-needed"
        self.github_bot_quick_start = "https://github.com/albertopoljak/Licensy#quickstart-bot-usage"
        self.github_faq = "https://github.com/albertopoljak/Licensy/wiki/FAQ"

    def cog_unload(self):
        """
        Revert to default help command in case cog is unloaded
        """
        self.bot.help_command = self._original_help_command

    @commands.command()
    async def faq(self, ctx):
        """
        Show common Q/A about bot and its usage.
        """
        bot_faq = (f"You can find it on [Github.]({self.github_faq})\n\n"
                   f"Please let me know which features/improvements you want so I can focus on those.\n"
                   f"Type `{ctx.prefix}support` for invite to support server.")
        await ctx.send(embed=info(bot_faq, ctx.me, title="FAQ"))

    @commands.command()
    async def quickstart(self, ctx):
        """
        Shortly explains first time bot usage.
        """
        description = f"See Github [quickstart link]({self.github_bot_quick_start})."
        await ctx.send(embed=info(description, ctx.me, title="Quickstart :)"))


def setup(bot):
    bot.add_cog(Help(bot))
