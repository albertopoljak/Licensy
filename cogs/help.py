import logging
import discord
from discord.ext import commands
from helpers.embed_handler import info
from helpers.misc import embed_space, get_top_role_color

logger = logging.getLogger(__name__)


class PrettyHelpCommand(commands.MinimalHelpCommand):
    def get_ending_note(self):
        command_name = self.invoked_with
        return "Type {0}{1} <command> for more info on a command.\n".format(self.clean_prefix, command_name)

    def get_opening_note(self):
        prefix = "If you like the bot please consider donating or starring the Github repository, ty :)"

        if self.context.guild is None:
            return prefix + "\n\nCalling help in DM will always show only basic commands:"
        elif self.context.author.guild_permissions.administrator:
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
        empty = discord.Embed.Empty
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(title=empty, description=page, color=get_top_role_color(self.context.me))
            await destination.send(embed=embed)


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
